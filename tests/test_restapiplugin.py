"""test_restapiplugin.py :: Tests for Fauxmo's `RESTAPIPlugin`."""

import json
import time
from multiprocessing import Process
from typing import Generator

import httpbin
import pytest
import requests
from restapiplugin import RESTAPIPlugin


config_path_str = "tests/test_restapiplugin_config.json"


@pytest.fixture(scope="function")
def restapiplugin_target() -> Generator:
    """Simulate the endpoints triggered by RESTAPIPlugin."""
    fauxmo_device = Process(
        target=httpbin.core.app.run,
        kwargs={"host": "127.0.0.1", "port": 8000},
        daemon=True,
    )

    fauxmo_device.start()
    time.sleep(1)

    yield

    fauxmo_device.terminate()
    fauxmo_device.join()


def test_restapiplugin_integration(
    fauxmo_server: pytest.fixture, restapiplugin_target: pytest.fixture
) -> None:
    """Test "on" and "off" actions for RESTAPIPlugin.

    This test uses requests to `post` a value to a Fauxmo device that
    simulates the way the Echo interacts with the Fauxmo server when it gets a
    request to turn something `on` or `off`.

    It requires both the Fauxmo server be running as well as a "target" HTTP
    server for Fauxmo to interact with.

    requests.post -> Fauxmo device running at `port` -> target url (httpbin
    in this case, from the device's `on_cmd`)
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
        resp_off = requests.post(base_url, data=data_off.encode())
        resp_state = requests.post(base_url, data=data_get_state.encode())

    assert resp_on.status_code == 200
    assert resp_off.status_code == 200
    assert resp_state.status_code == 200


def test_restapiplugin_unit(restapiplugin_target: pytest.fixture) -> None:
    """Test simple unit tests on just the device without the integration."""
    with open(config_path_str) as f:
        config: dict = json.load(f)

    for device_conf in config["PLUGINS"]["RESTAPIPlugin"]["DEVICES"]:
        device = RESTAPIPlugin(**device_conf)
        assert device.on() is True
        assert device.off() is True

        state = device.get_state()
        if device.state_cmd is not None:
            assert state == "on"
        else:
            assert state == "off"
