import json, os
from typing import Callable, Optional

class ChannelSetting:
    def __init__(self, recruitment_channel: Optional[int] = None, with_random_status: bool = False, with_live_status: bool = False, with_number_status: bool = True, can_edit_max_number: bool = False, max_number: Optional[int] = None):
        self.with_random_status = with_random_status
        self.with_live_status = with_live_status
        self.with_number_status = with_number_status
        self.can_edit_max_number = can_edit_max_number
        self.max_number = max_number
        self.recruitment_channel = recruitment_channel

    @classmethod
    def from_dict(cls, data):
        def get_bool(label: str, default_value: bool):
            return data[label] is True if label in data else default_value
        def get_optional_int(label: str, default_value: Optional[int]):
            num = data[label] if label in data else default_value
            if num is None or num is int:
                return num
            return None

        return cls(
            get_optional_int("recruitment_channel", None),
            get_bool("with_random_status", False),
            get_bool("with_live_status", False),
            get_bool("with_number_status", True),
            get_bool("can_edit_max_number", False),
            get_optional_int("max_number", None)
            )

class ChannelLiveSetting:
    def __init__(self, live_status: str, random_status: str, max_number: Optional[int], message: str):
        self.live_status = live_status
        self.random_status = random_status
        self.max_number = max_number
        self.message = message

class ChannelSettings:
    """
    The class representing a singleton that saves channel settings.
    """

    _instance = None
    file_path = "channel_settings.json"
    
    print(os.getcwd())

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChannelSettings, cls).__new__(cls)

            cls._instance._settings = {}

            if os.path.isfile(cls.file_path):
                with open(cls.file_path, "r") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        cls._instance._settings[int(key)] = ChannelSetting.from_dict(value)

        return cls._instance

    def __save(self):
        with open(self.file_path, "w") as f:
            json.dump({str(k): v.__dict__ for k, v in self._settings.items()}, f, indent=4)

    def edit_setting(self, category_id: int, editor: Callable[[ChannelSetting], None]):
        """
        Edit the settings for a specific category.
        """
        if category_id in self._settings:
            editor(self._settings[category_id])
        else:
            new_setting = ChannelSetting()
            editor(new_setting)
            self._settings[category_id] = new_setting
        self.__save()

    def get_setting(self, category_id: int) -> Optional[ChannelSetting]:
        if category_id in self._settings:
            return self._settings[category_id]
        return None
    