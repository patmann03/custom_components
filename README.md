# custom_components
Custom Components for Home Assistant

In your config directory, create a folder for 'custom_components' if it is not already there.  Place the litetouch folder inside.

On your configuration.yaml, add the component litetouch.  

Create the entities under the 'dimmers' section.  The addr field is your keypad number and the button number associated with the load.  The loadid is the index number on the loadgroup as it is defined in the liteware software.

Sample YAML
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
