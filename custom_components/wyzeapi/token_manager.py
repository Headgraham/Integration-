import logging
from inspect import iscoroutinefunction

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from wyzeapy.wyze_auth_lib import Token
from wyzeapy.exceptions import AccessTokenError, LoginError
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from .const import DOMAIN, ACCESS_TOKEN, REFRESH_TOKEN, REFRESH_TIME

_LOGGER = logging.getLogger(__name__)


class TokenManager:
    hass: HomeAssistant = None
    config_entry: ConfigEntry = None

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        TokenManager.hass = hass
        TokenManager.config_entry = config_entry

    @staticmethod
    async def token_callback(token: Token = None):
        _LOGGER.debug("TokenManager: Received new token, updating config entry.")
        if TokenManager.hass.config_entries.async_entries(DOMAIN):
            for entry in TokenManager.hass.config_entries.async_entries(DOMAIN):
                TokenManager.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        CONF_USERNAME: entry.data.get(CONF_USERNAME),
                        CONF_PASSWORD: entry.data.get(CONF_PASSWORD),
                        ACCESS_TOKEN: token.access_token,
                        REFRESH_TOKEN: token.refresh_token,
                        REFRESH_TIME: str(token.refresh_time),
                    },
                )


def token_exception_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            if iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        except (AccessTokenError, LoginError):
            _LOGGER.error("TokenManager detected a login issue and reset the stored entry.")
            if TokenManager.hass.config_entries.async_entries(DOMAIN):
                for entry in TokenManager.hass.config_entries.async_entries(DOMAIN):
                    await TokenManager.hass.config_entries.async_remove(entry.entry_id)

    return inner_function
