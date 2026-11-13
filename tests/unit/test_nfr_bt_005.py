import json

import pytest

from src.bluetooth.devices import DEFAULT_FIXTURE_PATH, Device, DuplicateDeviceIdError, load_devices


def write_fixture(tmp_path, entries):
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps({"devices": entries}), encoding="utf-8")
    return path


def entry(device_id, name="Test Phone A", passkey="123456"):
    return {"id": device_id, "name": name, "passkey": passkey}


@pytest.mark.positive
def test_nfr_bt_005_01_valid_device_record_loads(tmp_path):
    """TC-NFR-005-01 / NFR-BT-005"""
    path = write_fixture(tmp_path, [entry("DEV-001", "Test Phone A", "123456")])

    devices = load_devices(path)

    assert devices == [Device(id="DEV-001", name="Test Phone A", passkey="123456")]


@pytest.mark.positive
def test_nfr_bt_005_02_fixture_loads_from_shipped_file():
    """TC-NFR-005-02 / NFR-BT-005"""
    expected = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))["devices"]

    devices = load_devices(DEFAULT_FIXTURE_PATH)

    assert [(d.id, d.name, d.passkey) for d in devices] == [
        (e["id"], e["name"], e["passkey"]) for e in expected
    ]


@pytest.mark.boundary
def test_nfr_bt_005_03_shipped_fixture_has_at_least_7_devices():
    """TC-NFR-005-03 / NFR-BT-005"""
    devices = load_devices(DEFAULT_FIXTURE_PATH)

    assert len(devices) >= 7


@pytest.mark.edge
def test_nfr_bt_005_04_fixture_with_8_devices_loads_all_8(tmp_path):
    """TC-NFR-005-04 / NFR-BT-005"""
    entries = [entry(f"DEV-{n:03d}", f"Test Phone {n}", f"{n:06d}") for n in range(1, 9)]
    path = write_fixture(tmp_path, entries)

    devices = load_devices(path)

    assert len(devices) == 8
    assert [(d.id, d.name, d.passkey) for d in devices] == [
        (e["id"], e["name"], e["passkey"]) for e in entries
    ]


@pytest.mark.positive
def test_nfr_bt_005_05_every_shipped_device_is_valid():
    """TC-NFR-005-05 / NFR-BT-005"""
    devices = load_devices(DEFAULT_FIXTURE_PATH)

    for device in devices:
        assert device.id
        assert device.name
        assert len(device.passkey) == 6
        assert device.passkey.isascii() and device.passkey.isdigit()


@pytest.mark.positive
def test_nfr_bt_005_06_shipped_device_ids_are_unique():
    """TC-NFR-005-06 / NFR-BT-005"""
    devices = load_devices(DEFAULT_FIXTURE_PATH)

    ids = [device.id for device in devices]
    assert len(ids) == len(set(ids))


@pytest.mark.positive
@pytest.mark.skip(reason="Spec gap: no observable definition of 'synthetic placeholder' (no ID or name pattern defined)")
def test_nfr_bt_005_07_shipped_fixture_holds_synthetic_data_only():
    """TC-NFR-005-07 / NFR-BT-005"""
    raise NotImplementedError


@pytest.mark.boundary
def test_nfr_bt_005_25_two_entries_with_same_device_id_rejected(tmp_path):
    """TC-NFR-005-25 / NFR-BT-005"""
    path = write_fixture(tmp_path, [entry("DEV-001"), entry("DEV-001")])

    with pytest.raises(DuplicateDeviceIdError):
        load_devices(path)


@pytest.mark.negative
def test_nfr_bt_005_26_duplicate_id_with_different_name_and_passkey_rejected(tmp_path):
    """TC-NFR-005-26 / NFR-BT-005"""
    path = write_fixture(
        tmp_path,
        [entry("DEV-001", "Test Phone A", "123456"), entry("DEV-001", "Test Phone B", "654321")],
    )

    with pytest.raises(DuplicateDeviceIdError):
        load_devices(path)


@pytest.mark.negative
def test_nfr_bt_005_27_non_adjacent_duplicate_id_in_7_entries_rejected(tmp_path):
    """TC-NFR-005-27 / NFR-BT-005"""
    entries = [entry(f"DEV-{n:03d}") for n in range(1, 7)] + [entry("DEV-002")]
    path = write_fixture(tmp_path, entries)

    with pytest.raises(DuplicateDeviceIdError):
        load_devices(path)
