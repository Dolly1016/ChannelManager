from tkinter import NO
from typing import Awaitable, Callable, Optional
import discord
from discord import app_commands, Interaction
from discord.ext import commands

from ChannelSettings import ChannelSetting, ChannelSettings, SelectsSetting

class ConfirmView(discord.ui.View):
    def __init__(self, label: str, callback: Callable[[discord.Interaction], Awaitable[None]]):
        super().__init__(timeout=None)
        button_number = discord.ui.Button(label=label, style=discord.ButtonStyle.red, emoji="⚠")
        button_number.callback = callback
        self.add_item(button_number)

class CommandTree(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # main command group
    select_group = app_commands.Group(name="vcmg_selects", description="VCマネージャのセレクタ管理用コマンド群。")
    vc_group = app_commands.Group(name="vcmg_channels", description="VCマネージャのVC管理用コマンド群。")
    # sub command groups
    vc_edit_group = app_commands.Group(name="edit", parent=vc_group, description="管理対象のVCの詳細設定を編集するコマンド群。")
    vc_edit_selects_group = app_commands.Group(name="selects", parent=vc_group, description="管理対象のVCのセレクタ設定項目を編集するコマンド群。")

    async def __send_confirm_message(self, interaction: discord.Interaction, content: str, label: str, callback: Callable[[discord.Interaction], Awaitable[None]]):
        view = ConfirmView(label, callback)
        return await interaction.response.send_message(content, ephemeral=True, view=view)

    @select_group.command(name="new", description="新たなセレクタを追加します。")
    @app_commands.describe(identifier="他と重複しないセレクタの識別子。英大文字を推奨します。")
    @app_commands.describe(label="セレクタの表示上の名称。日本語を使用できます。")
    @app_commands.describe(default_value="セレクタの初期値。省略した場合、このセレクタは省略可能なセレクタとして扱われます。")
    @app_commands.describe(selection1="セレクタの選択項目。以降同様です。")
    async def select_new(self, interaction: discord.Interaction, identifier: str, label: str, default_value: Optional[str], selection1: Optional[str], selection2: Optional[str], selection3: Optional[str], selection4: Optional[str], selection5: Optional[str], selection6: Optional[str], selection7: Optional[str], selection8: Optional[str]):
        if ChannelSettings().get_selects_setting(identifier) is not None:
            await interaction.response.send_message(f"セレクタ {identifier} は既に登録済みです。", ephemeral=True)
            return

        valid_selections = [v for v in [selection1, selection2, selection3, selection4, selection5, selection6, selection7, selection8] if v is not None]

        def edit_setting(setting: SelectsSetting):
            setting.default_value = default_value
            setting.label = label
            setting.selects = valid_selections
        ChannelSettings().edit_selects_settings(identifier, edit_setting)
        await interaction.response.send_message(f"セレクタ {identifier} を追加しました。", ephemeral=True)

    @select_group.command(name="label", description="セレクタの表示上の名称を取得、あるいは変更します。")
    @app_commands.describe(identifier="セレクタの識別子。")
    @app_commands.describe(label="セレクタの表示上の名称。日本語を使用できます。省略すると現在の名称を表示します。")
    async def select_label(self, interaction: discord.Interaction, identifier: str, label: Optional[str]):
        setting = ChannelSettings().get_selects_setting(identifier)
        if setting is None:
            await interaction.response.send_message(f"セレクタ {identifier} が見つかりません。", ephemeral=True)
            return

        if label is None:
            await interaction.response.send_message(f"セレクタ {identifier} の現在の名称は`{setting.label}`です。", ephemeral=True)
            return

        def edit_setting(setting: SelectsSetting):
            setting.label = label
        ChannelSettings().edit_selects_settings(identifier, edit_setting)
        await interaction.response.send_message(f"セレクタ {identifier} の表示名を`{label}`に変更しました。", ephemeral=True)

    @select_group.command(name="remove", description="セレクタの選択項目を削除します。")
    @app_commands.describe(identifier="セレクタの識別子。")
    @app_commands.describe(index1="削除する選択項目の位置。位置は先頭を1番目として順に数えます。以降同様です。")
    async def select_remove(self, interaction: discord.Interaction, identifier: str, index1: int, index2: Optional[int], index3: Optional[int], index4: Optional[int], index5: Optional[int], index6: Optional[int], index7: Optional[int], index8: Optional[int]):
        setting = ChannelSettings().get_selects_setting(identifier)
        if setting is None:
            await interaction.response.send_message(f"セレクタ {identifier} が見つかりません。", ephemeral=True)
            return

        indices = [index1, index2, index3, index4, index5, index6, index7, index8]
        selects = [setting.selects[i - 1] for i in indices if i is not None and 0 < i <= len(setting.selects)]
        
        if len(selects) == 0:
            await interaction.response.send_message(f"削除できる項目がありません。", ephemeral=True)
            return

        content = "**◆コマンド実行の確認◆**\n以下の項目を削除します。よろしいですか？\n\n" + "\n".join(map(lambda v: "・" + v,selects))
        async def callback(interaction: discord.Interaction):
            def edit_setting(setting: SelectsSetting):
                for s in selects:
                    setting.selects.remove(s)
            ChannelSettings().edit_selects_settings(identifier, edit_setting)
            await interaction.response.send_message(f"セレクタ {identifier} から{len(selects)}個の項目を削除しました。", ephemeral=True)
        await self.__send_confirm_message(interaction, content, "すべて削除" if len(selects) > 1 else "削除", callback)

    @select_group.command(name="add", description="セレクタの選択項目を追加します。")
    @app_commands.describe(identifier="セレクタの識別子。")
    @app_commands.describe(selection1="追加する設定項目。以降同様です。")
    async def select_add(self, interaction: discord.Interaction, identifier: str, selection1: str, selection2: Optional[str], selection3: Optional[str], selection4: Optional[str], selection5: Optional[str], selection6: Optional[str], selection7: Optional[str], selection8: Optional[str]):
        setting = ChannelSettings().get_selects_setting(identifier)
        if setting is None:
            await interaction.response.send_message(f"セレクタ {identifier} が見つかりません。", ephemeral=True)
            return

        valid_selections = [v for v in [selection1, selection2, selection3, selection4, selection5, selection6, selection7, selection8] if v is not None]
        if len(valid_selections) == 0:
            await interaction.response.send_message(f"追加できる項目がありません。", ephemeral=True)
            return

        def edit_setting(setting: SelectsSetting):
            setting.selects.extend(valid_selections)
        ChannelSettings().edit_selects_settings(identifier, edit_setting)
        await interaction.response.send_message(f"セレクタ {identifier} に{len(valid_selections)}個の選択項目を追加しました。", ephemeral=True)

    @select_group.command(name="list", description="セレクタの一覧を表示します。")
    @app_commands.describe(identifier="指定しない場合、全セレクタの識別子一覧を表示します。セレクタの識別子を指定すると、そのセレクタの全設定項目を表示します。")
    async def select_list(self, interaction: discord.Interaction, identifier: Optional[str]):
        if identifier is None:
            message = "**◆全セレクタ一覧◆**\n\n" + "\n".join(map(lambda s: f"・{s} (表示名: {ChannelSettings().get_selects_setting(s).label})", ChannelSettings().get_all_selects()))
            await interaction.response.send_message(message, ephemeral=True)
            return
        
        setting = ChannelSettings().get_selects_setting(identifier)
        if setting is None:
            await interaction.response.send_message(f"セレクタ {identifier} が見つかりません。", ephemeral=True)
            return
        message = f"**◆セレクタ {identifier} 全設定項目一覧◆**\n\n" + "\n".join(map(lambda s: f"・{s}", setting.selects))
        await interaction.response.send_message(message, ephemeral=True)

    @vc_group.command(name="new", description="管理対象のVCを追加します。")
    @app_commands.describe(category_channel="VCを含むカテゴリチャンネル。このカテゴリに含まれる全VCが管理対象に追加されます。")
    @app_commands.describe(recruitment_channel="募集を掲示するテキストチャンネル。")
    @app_commands.describe(max_users="VCの募集人数。")
    @app_commands.describe(with_random_status="ゲーム中の雑談可否を表示するか。")
    @app_commands.describe(with_live_status="他ゲームの配信可否を表示するか。")
    @app_commands.describe(with_users_status="空き人数を表示するか。")
    @app_commands.describe(can_edit_max_users="VCごとの募集人数の変更を許可するか。")
    @app_commands.describe(category="入力履歴の記録カテゴリ。英大文字を推奨します。同カテゴリ間で入力履歴を共有します。")
    @app_commands.describe(selects="追加のセレクタ選択項目。")
    async def vc_new(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, recruitment_channel: Optional[discord.TextChannel], max_users: Optional[int], with_random_status: Optional[bool], with_live_status: Optional[bool], with_users_status: Optional[bool], can_edit_max_users: Optional[bool], category: Optional[str], selects: Optional[str]):
        if ChannelSettings().get_channel_setting(category_channel.id) is not None:
            await interaction.response.send_message(f"このカテゴリは既に登録済みです。", ephemeral=True)
            return 
        def edit_setting(channel_setting: ChannelSetting):
            channel_setting.recruitment_channel = recruitment_channel.id if recruitment_channel is not None else None
            channel_setting.max_number = max_users or channel_setting.max_number
            if with_random_status is not None:
               channel_setting.with_random_status = with_random_status
            if with_live_status is not None:
               channel_setting.with_live_status = with_live_status
            if with_users_status is not None:
               channel_setting.with_users_status = with_users_status
            if can_edit_max_users is not None:
               channel_setting.can_edit_max_users = can_edit_max_users
            channel_setting.category = category or "DEFAULT"
            if selects is not None:
                channel_setting.selects = [selects]

        ChannelSettings().edit_channel_setting(category_channel.id, edit_setting)
        await interaction.response.send_message(f"{category_channel.name} カテゴリを管理対象に追加しました。", ephemeral=True)

    @vc_group.command(name="remove", description="管理対象のVCを除外します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    async def vc_edit_recruitment(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, recruitment_channel: discord.TextChannel):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        ChannelSettings().remove_channel_setting()
        await interaction.response.send_message(f"{category_channel.name} カテゴリを管理対象から除外しました。", ephemeral=True)

    @vc_edit_group.command(name="recruitment", description="募集文の掲示先を変更します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    @app_commands.describe(recruitment_channel="募集を掲示するテキストチャンネル。")
    async def vc_edit_recruitment(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, recruitment_channel: Optional[discord.TextChannel]):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        def edit_setting(channel_setting: ChannelSetting):
            channel_setting.recruitment_channel = recruitment_channel.id if recruitment_channel is not None else None
        ChannelSettings().edit_channel_setting(category_channel.id, edit_setting)

        if recruitment_channel is None:
            await interaction.response.send_message(f"{category_channel.name} カテゴリを募集文掲載の対象から除外しました。", ephemeral=True)
        else:
            await interaction.response.send_message(f"{category_channel.name} カテゴリの掲示先を {recruitment_channel.name} チャンネルに変更しました。", ephemeral=True)

    @vc_edit_group.command(name="options", description="ON/OFFで切り替えられるオプションを編集します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    @app_commands.describe(with_random_status="ゲーム中の雑談可否を表示するか。")
    @app_commands.describe(with_live_status="他ゲームの配信可否を表示するか。")
    @app_commands.describe(with_users_status="空き人数を表示するか。")
    @app_commands.describe(can_edit_max_users="VCごとの募集人数の変更を許可するか。")
    async def vc_edit_options(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, with_random_status: Optional[bool], with_live_status: Optional[bool], with_users_status: Optional[bool], can_edit_max_users: Optional[bool]):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        def edit_setting(channel_setting: ChannelSetting):
            if with_random_status is not None:
               channel_setting.with_random_status = with_random_status
            if with_live_status is not None:
               channel_setting.with_live_status = with_live_status
            if with_users_status is not None:
               channel_setting.with_users_status = with_users_status
            if can_edit_max_users is not None:
               channel_setting.can_edit_max_users = can_edit_max_users
        ChannelSettings().edit_channel_settings(category_channel.id, edit_setting)
        await interaction.response.send_message(f"{category_channel.name} カテゴリのオプションを更新しました。", ephemeral=True)

    @vc_edit_group.command(name="max", description="デフォルトの最大募集人数を変更します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    @app_commands.describe(max_users="最大募集人数。")
    async def vc_edit_max(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, max_users: int):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        def edit_setting(channel_setting: ChannelSetting):
             channel_setting.max_number = max_users
        ChannelSettings().edit_channel_setting(category_channel.id, edit_setting)
        await interaction.response.send_message(f"{category_channel.name} カテゴリのデフォルトの最大募集人数を{max_users}人に変更しました。", ephemeral=True)

    @vc_edit_group.command(name="category", description="入力履歴の記録カテゴリを変更します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    @app_commands.describe(category="入力履歴の記録カテゴリ。英大文字を推奨します。同カテゴリ間で入力履歴を共有します。")
    async def vc_edit_category(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, category: str):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        def edit_setting(channel_setting: ChannelSetting):
             channel_setting.category = category
        ChannelSettings().edit_channel_setting(category_channel.id, edit_setting)
        await interaction.response.send_message(f"{category_channel.name} カテゴリの記録カテゴリを {category} に変更しました。", ephemeral=True)

    @vc_edit_selects_group.command(name="add", description="セレクタ設定項目を追加します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    @app_commands.describe(selects="セレクタの識別子。")
    async def vc_edit_selects_add(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, selects: str):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        if selects in settings.selects:
            await interaction.response.send_message(f"セレクタ {selects} は既に追加されています。", ephemeral=True)
            return 

        def edit_setting(channel_setting: ChannelSetting):
            channel_setting.selects.append(selects)
        ChannelSettings().edit_channel_setting(category_channel.id, edit_setting)
        await interaction.response.send_message(f"{category_channel.name} カテゴリでセレクタ {selects} を使用するようになりました。", ephemeral=True)

    @vc_edit_selects_group.command(name="remove", description="セレクタ設定項目を削除します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    @app_commands.describe(selects="セレクタの識別子。")
    async def vc_edit_selects_remove(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel, selects: str):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        if not selects in settings.selects:
            await interaction.response.send_message(f"セレクタ {selects} は追加されていません。", ephemeral=True)
            return 

        def edit_setting(channel_setting: ChannelSetting):
            channel_setting.selects.remove(selects)
        ChannelSettings().edit_channel_setting(category_channel.id, edit_setting)
        await interaction.response.send_message(f"{category_channel.name} カテゴリでセレクタ {selects} を使用しなくなりました。", ephemeral=True)

    @vc_group.command(name="list", description="管理対象の全カテゴリを確認します。")
    async def vc_list(self, interaction: discord.Interaction):
        channels = await interaction.guild.fetch_channels()
        def get_channel(channel_id: int):
            for channel in channels:
                if channel.id == channel_id:
                    return channel.name
            return "[ID: " + channel_id + "]"
        message = "**◆全カテゴリチャンネル一覧◆**\n\n" + "\n".join(map(lambda channel_id: f"・{get_channel(channel_id)}", ChannelSettings().get_all_channels()))
        await interaction.response.send_message(message, ephemeral=True)

    @vc_group.command(name="show", description="管理対象のカテゴリの詳細情報を確認します。")
    @app_commands.describe(category_channel="管理単位のカテゴリチャンネル。")
    async def vc_show(self, interaction: discord.Interaction, category_channel: discord.CategoryChannel):
        settings = ChannelSettings().get_channel_setting(category_channel.id)
        if settings is None:
            await interaction.response.send_message(f"管理対象外のカテゴリです。", ephemeral=True)
            return 

        message = f"**◆カテゴリ {category_channel.name} の詳細情報◆**\n\n"
        has_text_channel = settings.recruitment_channel is not None

        if has_text_channel:
            message += f"募集掲示先: {interaction.guild.get_channel(settings.recruitment_channel).mention}\n"
            if settings.max_number is not None:
                message += f"最大募集人数: {settings.max_number}人\n"
            message += f"ゲーム中の雑談可否: {'表示' if settings.with_random_status else '非表示'}\n"
            message += f"他ゲームの配信可否: {'表示' if settings.with_live_status else '非表示'}\n"
            message += f"空き人数の表示: {'表示' if settings.with_number_status else '非表示'}\n"
            message += f"VCごとの募集人数の変更: {'許可' if settings.can_edit_max_number else '禁止'}\n"
            message += f"入力履歴の記録カテゴリ: {settings.category}\n"
            if len(settings.selects) > 0:
                message += f"使用セレクタ: {', '.join(settings.selects)}\n"
        else:
            message += f"このカテゴリは募集が無効です。"

        await interaction.response.send_message(message, ephemeral=True)
        

async def setup(bot):
    await bot.add_cog(CommandTree(bot))