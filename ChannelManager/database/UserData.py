import sqlite3
from typing import Optional
from discord import Member
from ChannelSettings import ChannelLiveSetting, ChannelSetting

class UserTexts:
    def __init__(self):
        self.last_text_recruitment: Optional[str] = None
        self.last_text_random: Optional[str] = None
        self.last_text_random: Optional[str] = None
        self.last_text_live: Optional[str] = None
        self.templates: dict[str, str] = {}
        self.selects: dict[str, str] = {}

    def get_select(self, select_id: str) -> Optional[str]:
        if select_id in self.selects:
            return self.selects[select_id]
        return None
    

class UserData:
    """
    The class representing a singleton that saves users data.
    """

    _instance = None
    max_templates = 3

    last_text_recruitment = "LAST_RECRUITMENT"
    last_text_random = "LAST_RANDOM"
    last_text_live = "LAST_LIVE"
    templates_prefix = "TEMPLATE_"
    selects_prefix = "SELECTS_"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserData, cls).__new__(cls)
            cls._instance.connection = sqlite3.connect("user_data.db")
            cls._instance.cursor = cls._instance.connection.cursor()
            cls._instance.__create_tables_if_not_exist()
        return cls._instance
    
    def __create_tables_if_not_exist(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS USER_TEXTS (
                USER_ID TEXT,
                TYPE TEXT,
                TEXT TEXT,
                UNIQUE (USER_ID, TYPE)
            )
        ''')
        self.connection.commit()

    def get_user_texts(self, user: Member, category: str):
        user_id = str(user.id)
        search_pattern = f"{category}_%"
        
        self.cursor.execute('''
            SELECT USER_ID, TYPE, TEXT FROM USER_TEXTS
            WHERE USER_ID = ? AND TYPE LIKE ?
        ''', (user_id, search_pattern))
        
        results = self.cursor.fetchall()
        
        ut = UserTexts()
        for row in results:
            type_name = row[1][len(category) + 1:]
            if type_name == self.last_text_recruitment:
                ut.last_text_recruitment = row[2]
            elif type_name == self.last_text_random:
                ut.last_text_random = row[2]
            elif type_name == self.last_text_live:
                ut.last_text_live = row[2]
            elif type_name.startswith(self.templates_prefix):
                key = type_name[len(self.templates_prefix):]
                ut.templates[key] = row[2]    
            elif type_name.startswith(self.selects_prefix):
                key = type_name[len(self.selects_prefix):]
                ut.selects[key] = row[2]
        return ut

    def push_history(self, user: Member, live_setting: ChannelLiveSetting, channel_setting: ChannelSetting):
        """
        Update the last used texts for a user using UPSERT operation.
        """
        user_id = str(user.id)
        category = channel_setting.category
        
        updates = []
        
        # recruitment text
        if live_setting.message is not None:
            type_name = f"{category}_{self.last_text_recruitment}"
            updates.append((user_id, type_name, live_setting.message))
        
        # with random status
        if channel_setting.with_random_status and live_setting.random_status is not None:
            type_name = f"{category}_{self.last_text_random}"
            updates.append((user_id, type_name, live_setting.random_status))
        
        # with live status
        if channel_setting.with_live_status and live_setting.live_status is not None:
            type_name = f"{category}_{self.last_text_live}"
            updates.append((user_id, type_name, live_setting.live_status))
        
        for k, v in live_setting.selects.items():
            type_name = f"{category}_{self.selects_prefix}{k}"
            updates.append((user_id, type_name, v))

        # update the database
        for update in updates:
            self.cursor.execute('''
                INSERT INTO USER_TEXTS (USER_ID, TYPE, TEXT)
                VALUES (?, ?, ?)
                ON CONFLICT(USER_ID, TYPE) DO UPDATE SET 
                TEXT = excluded.TEXT
            ''', update)
        
        self.connection.commit()

    def push_template(self, user: Member, templates: dict[str,str], category: str):
        """
        Update the template text for a user using UPSERT operation.
        """
        user_id = str(user.id)
        
        # delete old templates
        template_search_pattern = f"{category}_{self.templates_prefix}%"
        self.cursor.execute('''
            DELETE FROM USER_TEXTS
            WHERE USER_ID = ? AND TYPE LIKE ?
        ''', (user_id, template_search_pattern))
        
        # insert new templates
        for key, text in templates.items():
            type_name = f"{category}_{self.templates_prefix}{key}"
            self.cursor.execute('''
                INSERT INTO USER_TEXTS (USER_ID, TYPE, TEXT)
                VALUES (?, ?, ?)
            ''', (user_id, type_name, text))
        
        self.connection.commit()

