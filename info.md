# LiteTouch Integration

{% if prerelease %}**This is a beta version!**{% endif %}

This integration uses [LiteTouch's RTC protocol](http://sav-documentation.s3.amazonaws.com/Internal%20Documentation/LiteTouch%20and%20Savant%20Lighting/5000,%205K%20-%20LiteTouch%20Integration%20Protocols.pdf) for interacting with the lighting system for use with Home Assistant.

Please see the [README](https://github.com/patmann03/custom_components/blob/master/README.md) for more details.

Note that you will need to restart Home Assistant after installation.


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