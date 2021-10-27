# custom_components
Custom Components for Home Assistant

# LiteTouch
In your config directory, create a folder for 'custom_components' if it is not already there.  Place the litetouch folder inside.

On your configuration.yaml, add the component litetouch.  

Create the entities under the 'dimmers' section.  The addr field is your keypad number and the button number associated with the load.  The loadid is the index number on the loadgroup as it is defined in the liteware software.

Sample YAML:

    litetouch:
      host: "192.168.1.65"
      port: 10001
      dimmers:
        - addr: "016_2"
          name: "Main Hall"
          loadid: "82"
        - addr: "4_7"
          name: "Front Hall Chandelier"
          loadid: "23"
      switch:
        - addr: "017_2"
          name: "Outside Outlets"
          loadid: "110"
          icon: mdi:power
          

# Opnsense Firewall Rule

download the opnsense_ruleswitch folder and place in custom_components folder within the Home Assistant config directory
Please NOTE that my rules are 'inverted'.  This means that this custom component shows the rule as off when it is enabled and on when it is disabled.  I use this to turn off the internet to PC/Xbox devices at night for the kid.  It is easier to say 'Internet is On' vs. firewall rule is on to disable internet for others in the house.


Sample YAML:
```
switch:
  - platform: opnsense_ruleswitch
    host: https://192.168.1.1/api
    api_key: <API KEY HERE OR !SECRET>
    access_token: <API Secret>
    rule_filter: HA
        
```        
Opnsense Setup:
```
    Install the os-firewall plugin
    Go to Firewall > Automation
    Create Rule
        NOTE: These rules are placed above all other rules (Automation > Floating > VLAN/LAN rules).  
        Be careful you you can lock yourself out.
    If you want to expose these to Home Assistant you can add: HA to the beginning of the rule (if you specify rule_filter in the home assistant config.yaml file).  
    Other rules would not be shown if you use the rule filter.
```
