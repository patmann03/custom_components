"""Support for LiteTouch Switch."""
import logging

from homeassistant.components.switch import SwitchDevice
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import (
    CONF_ADDR,
    CONF_SWITCH,
    CONF_LOADID,
    CONF_ICON,
    LITETOUCH_CONTROLLER,
    LiteTouchDevice,
)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discover_info=None):
    """Set up LiteTouch Switch."""
    if discover_info is None:
        return

    controller = hass.data[LITETOUCH_CONTROLLER]
    devs = []
    for switch in discover_info[CONF_SWITCH]:
        dev = LiteTouchSwitch(
            controller,
            switch[CONF_ADDR],
            switch[CONF_NAME],
            switch[CONF_LOADID],
            switch[CONF_ICON],
        )
        devs.append(dev)
    add_entities(devs, True)


class LiteTouchSwitch(LiteTouchDevice, SwitchDevice):
    """LiteTouch Switch."""

    def __init__(self, controller, addr, name, loadid, icon):
        """Create device with Addr, name, and loadid."""
        super().__init__(controller, addr, name)
        self._loadid = int(loadid)
        self._icon = icon
        self._state = 0

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        signal = f"litetouch_entity_{self._addr}"
        async_dispatcher_connect(self.hass, signal, self._update_callback)
        self._controller.get_led_states(self._addr)

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        self._controller.set_loadon(self._loadid)

    def turn_off(self, **kwargs):
        """Turn off the Switch."""
        self._controller.set_loadoff(self._loadid)

    @property
    def device_state_attributes(self):
        """Supported attributes."""
        return {"LiteTouch_address": self._addr, "Load ID: ": self._loadid}

    @property
    def is_on(self):
        """Is the Switch on/off."""
        return self._state != 0

    @property
    def icon(self):
        return self._icon

    @callback
    def _update_callback(self, msg_type, values):
        """Process device specific messages."""

        if msg_type == "RLEDU" or msg_type == "CGLES":
            _LOGGER.debug("Switch Update Callback: %s, %s", msg_type, values)
            lvl = int(values[1])
            if lvl == 1:
                self._state = 1
            else:
                self._state = 0

            self.async_schedule_update_ha_state()
