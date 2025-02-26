"""test_commandlineplugin.py :: Tests for Fauxmo's `CommandLinePlugin`.

For testing purposes, `on_cmd`s will run without error (return code 0) and
`off_cmd`s will have a return code other than 0 and therefore return False.
"""

import json

import pytest
import requests
from commandlineplugin import CommandLinePlugin


config_path_str = "tests/test_commandlineplugin_config.json"


def test_commandlineplugin_integration(fauxmo_server: pytest.fixture) -> None:
    """Test "on" and "off" actions for CommandLinePlugin.

    This test uses requests to `post` a value to a Fauxmo device that
    simulates the way the Echo interacts with the Fauxmo server when it gets a
    request to turn something `on` or `off`.
    """
    command_format = (
        "SOAPACTION: " '"urn:Belkin:service:basicevent:1#{}BinaryState"'.format
    )
    data_template = "<BinaryState>{}</BinaryState>".format

    data_get_state = command_format("Get")
    data_on = command_format("Set") + data_template(1)
    data_off = command_format("Set") + data_template(0)

    with fauxmo_server(config_path_str) as fauxmo_ip:
        base_url = f"http://{fauxmo_ip}:12345/upnp/control/basicevent1"
        resp_on = requests.post(base_url, data=data_on.encode())

        # Off command return code is not 0, so hangs and returns an error to
        # notify user that command failed
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.post(base_url, data=data_off.encode())

        resp_state = requests.post(base_url, data=data_get_state.encode())

    assert resp_on.status_code == 200
    assert resp_state.status_code == 200


def test_commandlineplugin_unit() -> None:
    """Test simpler unit tests on just the device without the integration."""
    with open(config_path_str) as f:
        config = json.load(f)

    for device_conf in config["PLUGINS"]["CommandLinePlugin"]["DEVICES"]:
        device = CommandLinePlugin(**device_conf)
        assert device.on() is True
        assert device.off() is False

        state = device.get_state()
        if device.state_cmd is None:
            assert state == "off"
        else:
            if "on state" in device.name:
                assert state == "on"
            elif "off state" in device.name:
                assert state == "off"
