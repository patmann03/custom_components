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
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

DOMAIN = "litetouch"

LITETOUCH_CONTROLLER = "litetouch"
ENTITY_SIGNAL = "litetouch_entity_{}"


CONF_DIMMERS = "dimmers"
CONF_SWITCH = "keypads"
CONF_ADDR = "addr"
CONF_LOADID = "loadid"


DIMMER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDR): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_LOADID): cv.string,
    }
)

KEYPAD_SCHEMA = vol.Schema(
    {vol.Required(CONF_ADDR): cv.string, vol.Required(CONF_NAME): cv.string}
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.port,
                vol.Required(CONF_DIMMERS): vol.All(cv.ensure_list, [DIMMER_SCHEMA]),
                vol.Optional(CONF_SWITCH, default=[]): vol.All(
                    cv.ensure_list, [KEYPAD_SCHEMA]
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
        addr = values[0]
        signal = ENTITY_SIGNAL.format(addr)
        _LOGGER.debug("send to dispatcher %s, %s, %s", signal, msg_type, values)
        dispatcher_send(hass, signal, msg_type, values)

    config = base_config.get(DOMAIN)
    _LOGGER.debug("Initiating connect to controller")
    controller = LiteTouch(config[CONF_HOST], config[CONF_PORT], hw_callback)
    hass.data[LITETOUCH_CONTROLLER] = controller

    def cleanup(event):
        controller.close()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup)

    dimmers = config[CONF_DIMMERS]
    load_platform(hass, "light", DOMAIN, {CONF_DIMMERS: dimmers}, base_config)

    for key_config in config[CONF_SWITCH]:
        addr = key_config[CONF_ADDR]
        name = key_config[CONF_NAME]
        LiteTouchKeypadEvent(hass, addr, name)

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


class LiteTouchKeypadEvent:
    """When you want signals instead of entities.

    Stateless sensors such as keypads are expected to generate an event
    instead of a sensor entity in hass.
    """

    def __init__(self, hass, addr, name):
        """Register callback that will be used for signals."""
        self._hass = hass
        self._addr = addr
        self._name = name
        self._id = slugify(self._name)
        signal = ENTITY_SIGNAL.format(self._addr)
        async_dispatcher_connect(self._hass, signal, self._update_callback)

    @callback
    def _update_callback(self, msg_type, values):
        """Fire events if button is pressed or released."""
        _LOGGER.debug("Update Callback keypad %s, %s", msg_type, values)
        if msg_type == HW_BUTTON_PRESSED:
            event = EVENT_BUTTON_PRESS
        elif msg_type == HW_BUTTON_RELEASED:
            event = EVENT_BUTTON_RELEASE
        else:
            return
        data = {CONF_ID: self._id, CONF_NAME: self._name, "button": values[1]}
        self._hass.bus.async_fire(event, data)
