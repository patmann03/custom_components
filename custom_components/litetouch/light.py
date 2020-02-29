"""Support for LiteTouch lights."""
import logging

import pylitetouch.pylitetouch

from homeassistant.components.light import ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import (
    CONF_ADDR,
    CONF_DIMMERS,
    CONF_LOADID,
    ENTITY_SIGNAL,
    LITETOUCH_CONTROLLER,
    LiteTouchDevice,
)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discover_info=None):
    """Set up LiteTouch lights."""
    if discover_info is None:
        return

    controller = hass.data[LITETOUCH_CONTROLLER]
    devs = []
    for dimmer in discover_info[CONF_DIMMERS]:
        dev = LiteTouchLight(
            controller, dimmer[CONF_ADDR], dimmer[CONF_NAME], dimmer[CONF_LOADID]
        )
        devs.append(dev)
    add_entities(devs, True)


class LiteTouchLight(LiteTouchDevice, Light):
    """LiteTouch Light."""

    def __init__(self, controller, addr, name, loadid):
        """Create device with Addr, name, and loadid."""
        super().__init__(controller, addr, name)
        self._loadid = int(loadid)
        self._level = 0
        self._prev_level = 0

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        signal = ENTITY_SIGNAL.format(self._addr)
        _LOGGER.debug("connecting %s", signal)
        async_dispatcher_connect(self.hass, signal, self._update_callback)
        self._controller.get_led_states(self._addr)

    @property
    def supported_features(self):
        """Supported features."""
        return SUPPORT_BRIGHTNESS

    def turn_on(self, **kwargs):
        """Turn on the light."""
        # _LOGGER.debug("Call turn on %s", **kwargs)
        if ATTR_BRIGHTNESS in kwargs:
            new_level = kwargs[ATTR_BRIGHTNESS]
        elif self._prev_level == 0:
            new_level = 255
        else:
            new_level = self._prev_level
        self._set_brightness(new_level)

    def turn_off(self, **kwargs):
        """Turn off the light."""
        self._set_brightness(0)

    @property
    def brightness(self):
        """Control the brightness."""
        return self._level

    def _set_brightness(self, level):
        """Send the brightness level to the device."""
        lid = str(self._loadid)
        _LOGGER.debug("Set Brightness on loadid %s, %s", lid, level)
        self._controller.set_loadlevel(self._loadid, int((level * 100) / 255))

    @property
    def device_state_attributes(self):
        """Supported attributes."""
        return {"LiteTouch_address": self._addr}

    @property
    def is_on(self):
        """Is the light on/off."""
        return self._level != 0

    @callback
    def _update_callback(self, msg_type, values):
        """Process device specific messages."""
        _LOGGER.debug("Light Callback: %s, %s", msg_type, values)
        if msg_type == "RLEDU" or msg_type == "CGLES":
            _LOGGER.debug(f" LT CB msg type: {msg_type}")
            lvl = int(values[1])
            if lvl == 1:
                self._level = 255
            else:
                self._level = 0
            if self._level != 0:
                self._prev_level = self._level
            self.async_schedule_update_ha_state()
