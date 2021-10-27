"""
Switch Platform support for opnSense firewall rules.

For more details please refer to
https://github.com/dgshue/home-assistant-custom-components

Example usage:

configuration.yaml

---------------------------------------

switch:
  - platform: opnsense_rule
    host: https://192.168.1.1/api
    api_key: PFFA1QDKsakjied21
    access_token: AectmzLxeTS413I6FtLyA3xhFxs3Y80n3bZEu6gzboxd5adUbbrejFZae1u5
    rule_filter: HomeAssistant


---------------------------------------

"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.switch import SwitchEntity
from homeassistant.components.switch import  PLATFORM_SCHEMA#(), ENTITY_ID_FORMAT)
from homeassistant.const import (
    CONF_FRIENDLY_NAME,  CONF_VALUE_TEMPLATE, CONF_HOST, CONF_API_KEY, CONF_ACCESS_TOKEN) #CONF_SWITCHES

CONF_RULE_FILTER = 'rule_filter'

DOMAIN = "switch"
DEFAULT_ICON_ENABLED = 'mdi:check-network-outline'
DEFAULT_ICON_DISABLED = 'mdi:close-network-outline'

REQUIREMENTS = ['pyopnsense==0.0.3']


_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_ACCESS_TOKEN): cv.string,
    vol.Optional(CONF_FRIENDLY_NAME): cv.string,
    vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
    vol.Optional(CONF_RULE_FILTER): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Initialize the platform"""

    """Setup the opnSense Rules platform."""
    #import pprint, sys
    from pyopnsense import client

    # Assign configuration variables. The configuration check takes care they are
    # present.
    host = config.get(CONF_HOST)
    api_key = config.get(CONF_API_KEY)
    access_token = config.get(CONF_ACCESS_TOKEN)
    rule_prefix = config.get(CONF_RULE_FILTER)

    _LOGGER.debug("Connecting to opnSense firewall to collect rules to add as switches.")

    try:
        
        opnsense = client.OPNClient(api_key, access_token,host)        

        filters = opnsense._get('firewall/filter/searchRule')

        _LOGGER.debug("Found %s rules in opnSense automation tab", (filters['total']))

        if rule_prefix:
            _LOGGER.debug("Filter for rules starting with %s being applied", rule_prefix)

        rules = []

        # Iterate through and find rules
        i = 0
        for rule in filters['rows']:
            tracker = rule.get('uuid')
            if tracker is None:
                _LOGGER.warning("Skipping rule (no tracker_id): " + rule['description'])
            else:
                if rule_prefix:
                    if (rule['description'].startswith(rule_prefix)):
                        _LOGGER.debug("Found rule %s", rule['description'])
                        new_rule = opnSense(opnsense, 'opnSense_'+rule['description'], rule['description'], tracker)
                        rules.append(new_rule)
                else:
                    _LOGGER.debug("Found rule %s", rule['description'])
                    new_rule = opnSense(opnsense, 'opnSense_'+rule['description'], rule['description'], tracker)
                    rules.append(new_rule)
            i=i+1

        # Add devices
        add_entities(rules, True)
    except Exception as e:
        _LOGGER.error("Problem getting rule set from opnSense host: %s.  Likely due to API key or secret. More Info:" + str(e), host)


class opnSense(SwitchEntity):    
    def __init__(self, opnsense, name, rule_name, uuid):
        _LOGGER.info("Initialized opnSense Rule SWITCH %s", name)
        """Initialize an opnSense Rule as a switch."""
        self._opnsense = opnsense
        self._name = name
        self._rule_name = rule_name
        self._state = None
        self._uuid = uuid

        
    
    @property
    def unique_id(self):
        """Return a unique identifier."""
        return f"opnsense.{self._uuid}"
    

    @property
    def device_state_attributes(self):
        """Supported attributes."""
        return {
            "UUID: ": self._uuid,
            "Rule Description: ": self._rule_name,
            
        }

    @property    
    def name(self):        
        """Name of the entity.""" 
        return self._name

    @property    
    def is_on(self): 
        """If the switch is currently on or off.""" 
        return self._state

    def turn_on(self, **kwargs):
        self.set_rule_state(True)

    def turn_off(self, **kwargs):
        self.set_rule_state(False)

    @property
    def icon(self):
        if self._state:
            return DEFAULT_ICON_ENABLED
        else:
            return DEFAULT_ICON_DISABLED

    def update(self):
        """Check the current state of the rule in OpnSense"""
        
        resp = self._opnsense._get(f"firewall/filter/getRule/{self._uuid}")
        _LOGGER.debug(resp)
        status = resp['rule']['enabled']

        if status == '1':
            self._state = False
        
        else:
            self._state = True
        




    def set_rule_state(self, action):
        """Set Firewall Rule."""


        resp = self._opnsense._post(f"firewall/filter/toggleRule/{self._uuid}","")

        status = resp['result']

        self._opnsense._post(f"firewall/filter/apply/","")

        if "Enabled" in status:
            self._state = False
        else:
            self._state = True

