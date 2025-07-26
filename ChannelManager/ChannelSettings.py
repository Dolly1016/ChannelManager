import json, os
from typing import Callable, Optional

from discord.ui import Select

class ChannelSetting:
    def __init__(self, recruitment_channel: Optional[int] = None, with_random_status: bool = False, with_live_status: bool = False, with_number_status: bool = True, can_edit_max_number: bool = False, max_number: Optional[int] = None, category: Optional[str] = None, selects: list[str] = []):
        self.with_random_status = with_random_status
        self.with_live_status = with_live_status
        self.with_number_status = with_number_status
        self.can_edit_max_number = can_edit_max_number
        self.max_number = max_number
        self.recruitment_channel = recruitment_channel
        self.category = category
        self.selects = selects

    @classmethod
    def from_dict(cls, data):
        def get_bool(label: str, default_value: bool):
            return data[label] is True if label in data else default_value
        def get_optional_int(label: str, default_value: Optional[int]):
            num = data[label] if label in data else default_value
            if isinstance(num, int):
                return num
            return None
        def get_str(label:str , default_value:str):
            val = data[label] if label in data else default_value
            if isinstance(val, str):
                return val
            return default_value
        def get_str_array(label:str):
            val = data[label] if label in data else []
            if isinstance(val, list):
                return  [item for item in val if isinstance(item, str)]
            return []

        return cls(
            get_optional_int("recruitment_channel", None),
            get_bool("with_random_status", True),
            get_bool("with_live_status", False),
            get_bool("with_number_status", True),
            get_bool("can_edit_max_number", False),
            get_optional_int("max_number", 4),
            get_str("category", "DEFAULT"),
            get_str_array("selects")
            )

class SelectsSetting:
    def __init__(self, label: Optional[str] = None, selects: list[str] = [], default_value: Optional[str] = None):
        self.label = label or self.error_select_label
        self.selects = selects
        self.default_value = default_value

    error_select_label = "不明な選択肢"

    @classmethod
    def from_dict(cls, data):
        def get_optional_str(label: str, default_value: Optional[str]):
            num = data[label] if label in data else default_value
            if isinstance(num, str):
                return num
            return None
        def get_str(label:str , default_value:str):
            val = data[label] if label in data else default_value
            if isinstance(val, str):
                return val
            return default_value
        def get_str_array(label:str):
            val = data[label] if label in data else []
            if isinstance(val, list):
                return  [item for item in val if isinstance(item, str)]
            return []

        return cls(
            get_str("label", cls.error_select_label),
            get_str_array("selects"),
            get_optional_str("default_value", None)
            )

class ChannelLiveSetting:
    def __init__(self, live_status: str, random_status: str, max_number: Optional[int], message: str, selects: dict[str,str]):
        self.live_status = live_status
        self.random_status = random_status
        self.max_number = max_number
        self.message = message
        self.selects = selects

class ChannelSettings:
    """
    The class representing a singleton that saves channel settings.
    """

    _instance = None
    channel_settings_path = "channel_settings.json"
    selects_settings_path = "selects_settings.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChannelSettings, cls).__new__(cls)

            cls._instance._channel_settings = {}
            if os.path.isfile(cls.channel_settings_path):
                with open(cls.channel_settings_path, "r", encoding='utf-8-sig') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        cls._instance._channel_settings[int(key)] = ChannelSetting.from_dict(value)

            cls._instance._selects_settings = {}
            if os.path.isfile(cls.selects_settings_path):
                with open(cls.selects_settings_path, "r", encoding='utf-8-sig') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        cls._instance._selects_settings[key] = SelectsSetting.from_dict(value)

        return cls._instance

    def __save_channels(self):
        with open(self.channel_settings_path, "w", encoding='utf-8-sig') as f:
            json.dump({str(k): v.__dict__ for k, v in self._channel_settings.items()}, f, indent=4)

    def remove_channel_setting(self, category_id: int):
        if category_id in self._channel_settings:
            self._channel_settings.pop(category_id)
            self.__save_channels()
            return True
        else:
            return False

    def get_channel_setting(self, category_id: int) -> Optional[ChannelSetting]:
        if category_id in self._channel_settings:
            return self._channel_settings[category_id]
        return None

    def edit_channel_setting(self, channel_id: int, editor: Callable[[ChannelSetting], None]):
        if channel_id in self._channel_settings:
            editor(self._channel_settings[channel_id])
        else:
            new_setting = ChannelSetting()
            editor(new_setting)
            self._channel_settings[channel_id] = new_setting
        self.__save_channels()

    def __save_selects(self):
        with open(self.selects_settings_path, "w", encoding='utf-8-sig') as f:
            json.dump({str(k): v.__dict__ for k, v in self._selects_settings.items()}, f, indent=4)
            
    def get_selects_setting(self, selects_id: str) -> Optional[SelectsSetting]:
        if selects_id in self._selects_settings:
            return self._selects_settings[selects_id]
        return None
    
    def edit_selects_settings(self, selects_id: str, editor: Callable[[SelectsSetting], None]):
        if selects_id in self._selects_settings:
            editor(self._selects_settings[selects_id])
        else:
            new_setting = SelectsSetting()
            editor(new_setting)
            self._selects_settings[selects_id] = new_setting
        self.__save_selects()

    def get_all_channels(self):
        return self._channel_settings.keys()

    def get_all_selects(self):
        return self._selects_settings.keys()
