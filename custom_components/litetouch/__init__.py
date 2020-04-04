"""Support for LiteTouch 5000LC and Savant SSL-P018 ."""
import logging


from pylitetouch.pylitetouch import LiteTouch
import voluptuous as vol

from homeassistant.const import (
    CONF_HOST,
    CONF_ID,
    CONF_NAME,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.util import slugify, dt

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIME_ZONE = dt.DEFAULT_TIME_ZONE

DOMAIN = "litetouch"

LITETOUCH_CONTROLLER = "litetouch"
ENTITY_SIGNAL = "litetouch_entity_{}"


CONF_DIMMERS = "dimmers"
CONF_SWITCH = "switch"
CONF_ADDR = "addr"
CONF_LOADID = "loadid"
CONF_ICON = "icon"
CONF_TOGGLE = "toggle"

DEF_ICON = "mdi:power-plug"
DEF_TOGGLE = "false"


DIMMER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDR): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_LOADID): cv.string,
        vol.Optional(CONF_TOGGLE, default=DEF_TOGGLE): cv.boolean,
    }
)

SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDR): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_LOADID): cv.string,
        vol.Optional(CONF_ICON, default=DEF_ICON): cv.icon,
        vol.Optional(CONF_TOGGLE, default=DEF_TOGGLE): cv.boolean,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.port,
                vol.Required(CONF_DIMMERS): vol.All(cv.ensure_list, [DIMMER_SCHEMA]),
                vol.Optional(CONF_SWITCH, default=[]): vol.All(
                    cv.ensure_list, [SWITCH_SCHEMA]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, base_config):
    """Start LiteTouch controller."""

    def hw_callback(msg_type, values):
        """Dispatch state changes."""
        _LOGGER.debug("callback: %s, %s", msg_type, values)
        # set entity id eq to callback value.
        addr = values[0]
        signal = f"litetouch_entity_{addr}"
        dispatcher_send(hass, signal, msg_type, values)

    config = base_config.get(DOMAIN)

    controller = LiteTouch(config[CONF_HOST], config[CONF_PORT], hw_callback)

    hass.data[LITETOUCH_CONTROLLER] = controller

    def cleanup(event):
        controller.close()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup)

    dimmers = config[CONF_DIMMERS]
    load_platform(hass, "light", DOMAIN, {CONF_DIMMERS: dimmers}, base_config)
    
    switch = config[CONF_SWITCH]
    load_platform(hass, "switch", DOMAIN, {CONF_SWITCH: switch}, base_config)

    def set_clock(call):
        time = dt.now(DEFAULT_TIME_ZONE)
        hass.states.set("litetouch.set_clock", time)
        clock = time.strftime("%Y%m%d%H%M%S")
        controller.set_clock(clock)

    hass.services.register(DOMAIN, "Set Clock", set_clock)

    return True


class LiteTouchDevice:
    """Base class of a litetouch device."""

    def __init__(self, controller, addr, name):
        """Initialize litetouch device."""

        # Ensure keypad is 3 digits.
        fixaddr = addr.split("_")[0]
        but = addr.split("_")[1]
        fixaddr = str(fixaddr).zfill(3)
        addr = fixaddr + "_" + but

        self._addr = addr
        self._name = name
        self._controller = controller

    @property
    def unique_id(self):
        """Return a unique identifier."""
        return f"litetouch.{self._addr}"

    @property
    def name(self):
        """Device name."""
        return self._name

    @property
    def should_poll(self):
        """No need to poll."""
        return False
