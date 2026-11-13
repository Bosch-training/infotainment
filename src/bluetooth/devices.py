import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "test-data" / "bluetooth-devices.json"


class DuplicateDeviceIdError(ValueError):
    pass


@dataclass(frozen=True)
class Device:
    id: str
    name: str
    passkey: str


def load_devices(path=DEFAULT_FIXTURE_PATH):
    with open(path, encoding="utf-8") as fixture_file:
        entries = json.load(fixture_file)["devices"]

    devices = []
    seen_ids = set()
    for entry in entries:
        device = Device(id=entry["id"], name=entry["name"], passkey=entry["passkey"])
        if device.id in seen_ids:
            raise DuplicateDeviceIdError(device.id)
        seen_ids.add(device.id)
        devices.append(device)
    return devices
