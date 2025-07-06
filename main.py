import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
import traceback
import datetime
import asyncio
import os
import json
import requests
import threading 

#Token系
TOKEN = "MTM4OTg2MzQ4NzgyMzY3NTQ0Mg.G249Zn.SJ2uZ08smU1hHIT5pC08dVFaCDG4SypiL9fJds"
OWNER_ID = 1347987555177467914

LOG_CONFIG_PATH = "log_config.json"

def load_log_config():
    if not os.path.exists(LOG_CONFIG_PATH):
        return {}
    with open(LOG_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_log_config(config):
    with open(LOG_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

STARTUP_LOG_CHANNEL_ID = 1386951634474766336
ERROR_LOG_CHANNEL_ID = 1386952140941033502
GUILD_LOG_CHANNEL_ID = 1386951790926499971

@tasks.loop(minutes=1)
async def update_status():
    total_guilds = len(bot.guilds)
    total_users = sum(g.member_count for g in bot.guilds)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{total_guilds}サーバー | {total_users}ユーザー"
            
        )
    )

@bot.event
async def on_ready():
    await tree.sync()
    print(f"{bot.user} ✅Logined！")

    update_status.start()

    ch = bot.get_channel(STARTUP_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title="✅Bot起動ログ", description=f"{bot.user.name} が起動しました。", color=discord.Color.green())
        embed.add_field(name="導入数", value=f"{len(bot.guilds)} サーバー", inline=False)
        total_users = sum(g.member_count for g in bot.guilds)
        embed.add_field(name="総ユーザー数", value=str(total_users))
        embed.timestamp = datetime.datetime.utcnow()
        await ch.send(embed=embed)


@bot.event
async def on_guild_join(guild):
    ch = bot.get_channel(GUILD_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title="📥 Bot導入", description=f"{guild.name} に導入されました。", color=discord.Color.green())
        embed.add_field(name="サーバーID", value=str(guild.id))
        embed.add_field(name="メンバー数", value=str(guild.member_count))
        embed.timestamp = datetime.datetime.utcnow()
        await ch.send(embed=embed)

@bot.event
async def on_guild_remove(guild):
    ch = bot.get_channel(GUILD_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title="📤 Bot退出", description=f"{guild.name} から退出しました。", color=discord.Color.red())
        embed.add_field(name="サーバーID", value=str(guild.id))
        embed.add_field(name="メンバー数", value=str(guild.member_count))
        embed.timestamp = datetime.datetime.utcnow()
        await ch.send(embed=embed)


@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return

    config = load_log_config()
    guild_id = str(message.guild.id)
    channel_id = config.get(guild_id, {}).get("message_delete")
    if not channel_id:
        return

    ch = bot.get_channel(channel_id)
    if ch:
        embed = discord.Embed(title="🗑️ メッセージ削除", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="ユーザー", value=f"{message.author} (`{message.author.id}`)", inline=False)
        embed.add_field(name="チャンネル", value=message.channel.mention, inline=False)
        embed.add_field(name="内容", value=message.content or "（埋め込み/画像など）", inline=False)
        await ch.send(embed=embed)
@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild or before.content == after.content:
        return

    config = load_log_config()
    guild_id = str(before.guild.id)
    channel_id = config.get(guild_id, {}).get("message_edit")
    if not channel_id:
        return

    ch = bot.get_channel(channel_id)
    if ch:
        embed = discord.Embed(title="✏️ メッセージ編集", color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="ユーザー", value=f"{before.author} (`{before.author.id}`)", inline=False)
        embed.add_field(name="チャンネル", value=before.channel.mention, inline=False)
        embed.add_field(name="前", value=before.content or "（空）", inline=False)
        embed.add_field(name="後", value=after.content or "（空）", inline=False)
        await ch.send(embed=embed)
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    config = load_log_config()
    guild_id = str(message.guild.id)
    channel_id = config.get(guild_id, {}).get("invite_create")
    if not channel_id:
        return

    if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
        ch = bot.get_channel(channel_id)
        if ch:
            embed = discord.Embed(title="🔗 招待リンク検知", color=discord.Color.yellow(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="ユーザー", value=f"{message.author} (`{message.author.id}`)", inline=False)
            embed.add_field(name="チャンネル", value=message.channel.mention, inline=False)
            embed.add_field(name="内容", value=message.content, inline=False)
            await ch.send(embed=embed)
@bot.event
async def on_member_join(member):
    config = load_log_config()
    guild_id = str(member.guild.id)
    channel_id = config.get(guild_id, {}).get("member_log")
    if not channel_id:
        return

    ch = bot.get_channel(channel_id)
    if ch:
        embed = discord.Embed(title="🟢 メンバー参加", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="ユーザー", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="サーバー", value=f"{member.guild.name}", inline=False)

        total_guilds = len(bot.guilds)
        total_users = sum(g.member_count for g in bot.guilds)
        embed.add_field(name="📊 現在の状況", value=f"サーバー数: {total_guilds}\nユーザー数: {total_users}", inline=False)

        await ch.send(embed=embed)
@bot.event
async def on_member_remove(member):
    config = load_log_config()
    guild_id = str(member.guild.id)
    channel_id = config.get(guild_id, {}).get("member_log")
    if not channel_id:
        return

    ch = bot.get_channel(channel_id)
    if ch:
        embed = discord.Embed(title="🔴 メンバー退出", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="ユーザー", value=f"{member.name}#{member.discriminator} (`{member.id}`)", inline=False)
        embed.add_field(name="サーバー", value=f"{member.guild.name}", inline=False)

        total_guilds = len(bot.guilds)
        total_users = sum(g.member_count for g in bot.guilds)
        embed.add_field(name="📊 現在の状況", value=f"サーバー数: {total_guilds}\nユーザー数: {total_users}", inline=False)

        await ch.send(embed=embed)




@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    log_channel = bot.get_channel(ERROR_LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title="⚠️ スラッシュコマンドエラー", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="ユーザー", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="サーバー", value=interaction.guild.name if interaction.guild else "DM", inline=False)
        embed.add_field(name="エラー内容", value=f"```{str(error)}```", inline=False)
        if interaction.command:
            embed.add_field(name="コマンド", value=interaction.command.name, inline=False)
        await log_channel.send(embed=embed)

    try:
        await interaction.response.send_message("⚠️ コマンド実行中にエラーが発生しました。", ephemeral=True)
    except:
        pass

@tree.command(name="broadcast", description="Bot導入済み全サーバーで @everyone にアナウンスを送信します（制作者専用）")
@app_commands.describe(message="送信するメッセージ")
async def broadcast(interaction: discord.Interaction, message: str):
    if interaction.user.id != OWNER_ID: 
        await interaction.response.send_message("❌ あなたはこのコマンドを使用できません。", ephemeral=True)
        return

    embed = discord.Embed(title="🌍 グローバルアナウンス", description=message, color=discord.Color.dark_gold())
    success = 0
    for guild in bot.guilds:
        target_channel = None

        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            target_channel = guild.system_channel
        else:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    target_channel = ch
                    break

        if target_channel:
            try:
                await target_channel.send(content="@everyone", embed=embed)
                success += 1
            except Exception as e:
                log_channel = bot.get_channel(ERROR_LOG_CHANNEL_ID)
                if log_channel:
                    error_embed = discord.Embed(
                        title="📡 アナウンス送信エラー",
                        description=f"**サーバー:** {guild.name} (`{guild.id}`)\n```{e}```",
                        color=discord.Color.red()
                    )
                    await log_channel.send(embed=error_embed)
                continue

    await interaction.response.send_message(f"✅ {success} サーバーにアナウンスを送信しました。", ephemeral=True)

@tree.command(name="nuke", description="チャンネルを爆破して再生成します（管理者専用）")
@app_commands.checks.has_permissions(administrator=True)
async def nuke(interaction: discord.Interaction):
    try:
        old = interaction.channel
        new = await old.clone(reason="Nuke")
        await old.delete()
        embed = discord.Embed(title="💣 チャンネル爆破完了", description=f"{new.mention} を作成しました。", color=discord.Color.red())
        await new.send(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)
        log = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if log:
            err = discord.Embed(title="❌ Nuke エラー", description=f"```\n{e}\n```", color=discord.Color.red())
            await log.send(embed=err)

@tree.command(name="kick", description="ユーザーをキックします（管理者専用）")
@app_commands.describe(user="キックするユーザー", reason="理由")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "理由なし"):
    try:
        await user.kick(reason=reason)
        embed = discord.Embed(title="👢 キック成功", description=f"{user.mention} をキックしました。", color=discord.Color.orange())
        embed.add_field(name="理由", value=reason)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)
        log = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if log:
            err = discord.Embed(title="❌ Kick エラー", description=f"```\n{e}\n```", color=discord.Color.red())
            await log.send(embed=err)

@tree.command(name="ban", description="ユーザーをBANします（管理者専用）")
@app_commands.describe(user="BANするユーザー", reason="理由")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "理由なし"):
    try:
        await user.ban(reason=reason)
        embed = discord.Embed(title="⛔ BAN成功", description=f"{user.mention} をBANしました。", color=discord.Color.dark_red())
        embed.add_field(name="理由", value=reason)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)
        log = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if log:
            err = discord.Embed(title="❌ BAN エラー", description=f"```\n{e}\n```", color=discord.Color.red())
            await log.send(embed=err)

@tree.command(name="timeout", description="ユーザーを一時ミュートします（管理者専用）")
@app_commands.describe(user="対象ユーザー", minutes="ミュート時間（分）", reason="理由")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "理由なし"):
    try:
        until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
        await user.timeout(until, reason=reason)
        embed = discord.Embed(title="⏰ タイムアウト", description=f"{user.mention} を {minutes} 分ミュートしました。", color=discord.Color.purple())
        embed.add_field(name="理由", value=reason)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)
        log = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if log:
            err = discord.Embed(title="❌ Timeout エラー", description=f"```\n{e}\n```", color=discord.Color.red())
            await log.send(embed=err)

@tree.command(name="nickname", description="ニックネームを変更します（管理者専用）")
@app_commands.describe(user="対象ユーザー", nickname="新しいニックネーム")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nickname(interaction: discord.Interaction, user: discord.Member, nickname: str):
    try:
        await user.edit(nick=nickname)
        embed = discord.Embed(title="✏️ ニックネーム変更", description=f"{user.mention} のニックネームを `{nickname}` に変更しました。", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)
        log = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if log:
            err = discord.Embed(title="❌ ニックネーム変更エラー", description=f"```\n{e}\n```", color=discord.Color.red())
            await log.send(embed=err)

@tree.command(name="avatar", description="指定ユーザーのアイコンを表示します")
@app_commands.describe(user="対象のユーザー")
async def avatar(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    embed = discord.Embed(title=f"{user.name} のアイコン", color=discord.Color.blue())
    embed.set_image(url=user.display_avatar.url)
    embed.set_footer(text="画像を右クリックで保存できます")
    await interaction.response.send_message(embed=embed)

@tree.command(name="server_id", description="このサーバーのIDを表示します")
async def server_id(interaction: discord.Interaction):
    embed = discord.Embed(title="🆔 サーバーID", description=f"`{interaction.guild.id}`", color=discord.Color.greyple())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="roleall", description="指定ロールを全員に付与します（管理者専用）")
@app_commands.describe(role="付与するロール")
@app_commands.checks.has_permissions(administrator=True)
async def roleall(interaction: discord.Interaction, role: discord.Role):
    count = 0
    await interaction.response.defer(thinking=True)
    for member in interaction.guild.members:
        if not member.bot and role not in member.roles:
            try:
                await member.add_roles(role)
                count += 1
            except:
                continue
    await interaction.followup.send(f"✅ {count}人にロール `{role.name}` を付与しました。")

@tree.command(name="help", description="Botの全コマンド一覧と説明を表示します")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 パクパクBOT コマンド一覧",
        description="以下はこのBotの全機能一覧です：",
        color=discord.Color.teal()
    )

    embed.add_field(
        name="🛠️ 管理者コマンド",
        value=(
            "`/ban` - ユーザーをBAN\n"
            "`/kick` - ユーザーをキック\n"
            "`/timeout` - タイムアウトを設定\n"
            "`/nickname` - ニックネームを変更\n"
            "`/nuke` - チャンネルを初期化\n"
            "`/serverreset` - サーバー完全初期化\n"
            "`/say` - Botにメッセージを発言させる\n"
        ),
        inline=False
    )

    embed.add_field(
        name="📦 バックアップ",
        value=(
            "`/backup` - サーバー構成をバックアップ\n"
            "`/restore` - バックアップから復元"
        ),
        inline=False
    )

    embed.add_field(
        name="🔄 ユーティリティ",
        value=(
            "`/poll` - 投票パネル作成\n"
            "`/broadcast` - 全サーバーに@everyoneで告知（開発者専用）\n"
            "`/announce` - このサーバーで@everyoneアナウンス\n"
            "`/reactionpanel` - リアクションでロール取得パネル作成\n"
            "`/giveall` - 指定ロールを全員に配布\n"
            "`/forward` - サーバー間でメッセージ転送"
        ),
        inline=False
    )

    embed.add_field(
        name="🧾 プロフィール・情報",
        value=(
            "`/profile` - ユーザープロフィール表示\n"
            "`/avatar` - ユーザーのアイコン取得\n"
            "`/server_id` - サーバーIDを表示\n"
            "`/usercount` - 認証済み人数を表示"
        ),
        inline=False
    )

    embed.add_field(
        name="🧩 システム・UI",
        value=(
            "`/logpanel` - ログ記録設定UIを表示\n"
            "`/verify` - 認証パネル作成\n"
            "`/reactionpanel` - リアクションロール\n"
            "`/call` - 登録ユーザーをサーバーに追加\n"
            "`/datacheck` - 登録数を表示（制作者専用）"
        ),
        inline=False
    )

    embed.add_field(
        name="🎟️ チケット・実績",
        value=(
            "`/ticket` - チケット作成パネル\n"
            "`/achievement` - 実績投稿\n"
            "`/achlog` - 実績の投稿先チャンネルを設定"
        ),
        inline=False
    )

    embed.set_footer(text="🧠 パクパクBot ヘルプ | 最新状態で自動更新")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="poll", description="簡易投票を作成します")
@app_commands.describe(title="投票のタイトル", option1="選択肢1", option2="選択肢2")
async def poll(interaction: discord.Interaction, title: str, option1: str, option2: str):
    embed = discord.Embed(title=f"📊 {title}", color=discord.Color.blue())
    embed.add_field(name="1️⃣", value=option1, inline=False)
    embed.add_field(name="2️⃣", value=option2, inline=False)
    message = await interaction.channel.send(embed=embed)
    await message.add_reaction("1️⃣")
    await message.add_reaction("2️⃣")
    await interaction.response.send_message("✅ 投票を作成しました。", ephemeral=True)

@bot.tree.command(name='verify', description='認証パネルをこのチャンネルに設置します')
@app_commands.describe(role='認証時に付与するロール名')
async def verify(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("エラー: このコマンドを使用するには管理者権限が必要です。", ephemeral=True)
        return

    bot_member = interaction.guild.get_member(bot.user.id)
    if role.position >= bot_member.top_role.position:
        await interaction.response.send_message("このロールはボットよりも権限が上です。", ephemeral=True)
        return

    embed = discord.Embed(title="認証", description="下記のボタンをおして認証を完了してください", color=discord.Color.blue())
    view = discord.ui.View(timeout=None)
    button = discord.ui.Button(label="✅ 認証", style=discord.ButtonStyle.green)

    async def button_callback(interaction: discord.Interaction):
        if role in interaction.user.roles:
            await interaction.response.send_message("既にこのロールを持っています。", ephemeral=True)
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"認証が完了しました。{role.mention} を付与しました。", ephemeral=True)

    button.callback = button_callback
    view.add_item(button)
    await interaction.response.send_message(embed=embed, view=view)

    
from random import sample

active_giveaways = {}

class GiveawayView(discord.ui.View):
    def __init__(self, message_id, interaction, prize, winners):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.interaction = interaction
        self.prize = prize
        self.winners = winners
        self.ended = False

    @discord.ui.button(label="⛔ 強制終了", style=discord.ButtonStyle.red)
    async def force_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("❌ あなたはこの操作を実行できません。", ephemeral=True)
            return

        if self.ended:
            await interaction.response.send_message("⚠️ すでに終了しています。", ephemeral=True)
            return

        self.ended = True
        await self.end_giveaway()

    async def end_giveaway(self):
        msg = await self.interaction.channel.fetch_message(self.message_id)
        users = [u async for u in msg.reactions[0].users() if not u.bot]
        if len(users) < self.winners:
            result = "❌ 参加者不足により当選者なし"
        else:
            selected = sample(users, k=self.winners)
            result = "🎉 当選者: " + ", ".join(u.mention for u in selected)

        await self.interaction.channel.send(result)
        self.stop()
        active_giveaways.pop(self.message_id, None)

@tree.command(name="giveaway", description="抽選を作成します（管理者専用）")
@app_commands.describe(
    prize="景品名",
    winners="当選者数",
    duration_minutes="抽選終了までの時間（分）"
)
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, prize: str, winners: int = 1, duration_minutes: int = 1):
    duration_seconds = duration_minutes * 60

    embed = discord.Embed(
        title="🎁 ギブウェイ開催！",
        description=f"景品: **{prize}**\nリアクションで参加！\n🎉 終了まで {duration_minutes} 分",
        color=discord.Color.gold()
    )
    embed.set_footer(text="終了時にランダムで当選者を選びます")

    await interaction.response.send_message("✅ ギブウェイを開始しました。", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🎉")

    view = GiveawayView(message_id=msg.id, interaction=interaction, prize=prize, winners=winners)
    active_giveaways[msg.id] = view
    await msg.edit(view=view)

    await asyncio.sleep(duration_seconds)

    if msg.id not in active_giveaways:
        return

    view.ended = True
    await view.end_giveaway()


@tree.command(name="achievement", description="実績投稿パネルを送信します（管理者専用）")
@app_commands.describe(channel="投稿先チャンネル")
@app_commands.checks.has_permissions(administrator=True)
async def achievement(interaction: discord.Interaction, channel: discord.TextChannel):
    class AchievementModal(Modal, title="🏆 実績レビュー"):
        item = TextInput(label="実績タイトル", max_length=50)
        rating = TextInput(label="評価（1〜5）", max_length=1)
        comment = TextInput(label="感想", style=discord.TextStyle.paragraph)

        async def on_submit(self, interaction2: discord.Interaction):
            embed = discord.Embed(title=f"🏅 {self.item.value}", color=discord.Color.orange())
            embed.add_field(name="評価", value=f"{self.rating.value} / 5", inline=False)
            embed.add_field(name="感想", value=self.comment.value, inline=False)
            embed.set_footer(text=f"ユーザー: {interaction2.user}")
            await channel.send(embed=embed)
            await interaction2.response.send_message("✅ 実績を投稿しました。", ephemeral=True)

    class AchievementButton(View):
        @discord.ui.button(label="📩 実績を送信", style=discord.ButtonStyle.primary)
        async def open_modal(self, interaction2: discord.Interaction, button: Button):
            await interaction2.response.send_modal(AchievementModal())

    await interaction.response.send_message(
        embed=discord.Embed(title="🏆 実績パネル", description="以下のボタンから実績を投稿してください。", color=discord.Color.gold()),
        view=AchievementButton()
    )

@tree.command(name="ticket", description="チケットサポートパネルを表示します（管理者専用）")
@app_commands.describe(category="チケットを作るカテゴリ", role="対応スタッフのロール")
@app_commands.checks.has_permissions(administrator=True)
async def ticket(interaction: discord.Interaction, category: discord.CategoryChannel, role: discord.Role):
    class TicketView(View):
        @discord.ui.button(label="🎫 チケットを作成", style=discord.ButtonStyle.green)
        async def create_ticket(self, interaction2: discord.Interaction, button: Button):
            overwrites = {
                interaction2.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction2.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                role: discord.PermissionOverwrite(view_channel=True)
            }
            channel = await category.create_text_channel(f"ticket-{interaction2.user.name}", overwrites=overwrites)
            await channel.send(f"{interaction2.user.mention} さん、スタッフをお待ちください。")
            await interaction2.response.send_message(f"✅ チケットを作成しました: {channel.mention}", ephemeral=True)

    embed = discord.Embed(title="🎟️ チケット", description="質問や要望がある方はチケットを作成してください。", color=discord.Color.teal())
    await interaction.response.send_message(embed=embed, view=TicketView())

forwarding_channels = {} 

@tree.command(name="forward", description="メッセージ転送を開始/停止します（管理者専用）")
@app_commands.describe(source="送信元チャンネル", target="送信先チャンネル", stop="転送を停止する場合True")
@app_commands.checks.has_permissions(administrator=True)
async def forward(interaction: discord.Interaction, source: discord.TextChannel, target: discord.TextChannel, stop: bool = False):
    if stop:
        if source.id in forwarding_channels:
            del forwarding_channels[source.id]
            await interaction.response.send_message(f"🔁 転送を停止しました：{source.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ このチャンネルは転送対象ではありません。", ephemeral=True)
        return

    forwarding_channels[source.id] = target.id
    await interaction.response.send_message(
        embed=discord.Embed(
            title="🔄 メッセージ転送開始",
            description=f"{source.mention} → {target.mention} への転送を開始しました。",
            color=discord.Color.green()
        ), ephemeral=True
    )


@bot.event
async def on_message(message):


    if message.author.bot:
        return

    config = load_log_config()
    guild_id = str(message.guild.id)
    invite_channel_id = config.get(guild_id, {}).get("invite_create")
    if invite_channel_id and ("discord.gg/" in message.content or "discord.com/invite/" in message.content):
        ch = bot.get_channel(invite_channel_id)
        if ch:
            embed = discord.Embed(title="🔗 招待リンク検知", color=discord.Color.yellow(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="ユーザー", value=f"{message.author} (`{message.author.id}`)", inline=False)
            embed.add_field(name="チャンネル", value=message.channel.mention, inline=False)
            embed.add_field(name="内容", value=message.content, inline=False)
            await ch.send(embed=embed)

    if message.channel.id in forwarding_channels:
        target_id = forwarding_channels[message.channel.id]
        target = bot.get_channel(target_id)
        if target:
            try:
                await target.send(
                    embed=discord.Embed(
                        description=message.content,
                        color=discord.Color.light_grey()
                    ).set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                )
            except Exception as e:
                log = bot.get_channel(ERROR_LOG_CHANNEL_ID)
                if log:
                    await log.send(embed=discord.Embed(title="🚨 転送エラー", description=f"```\n{e}\n```", color=discord.Color.red()))

    await bot.process_commands(message)


reaction_role_messages = {}

@tree.command(name="reactionpanel", description="リアクションロールパネルを送信します（管理者専用）")
@app_commands.describe(role="付与したいロール", emoji="リアクション絵文字")
@app_commands.checks.has_permissions(administrator=True)
async def reactionpanel(interaction: discord.Interaction, role: discord.Role, emoji: str):
    embed = discord.Embed(
        title="🎭 リアクションでロールを取得！",
        description=f"{emoji} をリアクションすると `{role.name}` ロールが付与されます。",
        color=discord.Color.green()
    )
    message = await interaction.channel.send(embed=embed)
    await message.add_reaction(emoji)

    reaction_role_messages[message.id] = {
        "role_id": role.id,
        "emoji": emoji
    }

    await interaction.response.send_message("✅ リアクションパネルを作成しました。", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id not in reaction_role_messages:
        return
    data = reaction_role_messages[payload.message_id]
    if str(payload.emoji) != data["emoji"]:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    role = guild.get_role(data["role_id"])

    if role and member:
        await member.add_roles(role)
@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id not in reaction_role_messages:
        return
    data = reaction_role_messages[payload.message_id]
    if str(payload.emoji) != data["emoji"]:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    role = guild.get_role(data["role_id"])

    if role and member:
        await member.remove_roles(role) 
@tree.command(name="promote", description="Botの導入宣伝を送信します（管理者用）")
@app_commands.describe(channel="宣伝を送信するチャンネル")
@app_commands.checks.has_permissions(administrator=True)
async def promote(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = discord.Embed(
        title="📢 パクパクBotを導入しよう！",
        description=(
            "この多機能Bot「パクパク」をあなたのサーバーに導入しませんか？\n"
            "- ✅ 認証 / チケット / 実績 / ログ / 転送 など多数の機能\n"
            "- 🌐 完全日本語対応\n"
            "- 🛠️ コマンドで全て管理可能\n\n"
            "**今すぐ追加：[Botを招待する](https://discord.com/oauth2/authorize?client_id=1386666828977410160&permissions=8&integration_type=0&scope=bot)**\n"
            "**サポートサーバー：[サポートサーバーに参加](https://discord.gg/Zc69n3BvaB)**"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="made：mazika1u")
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ 宣伝を送信しました。", ephemeral=True)
    
# --- 最上部付近に追加 ---
DEVELOPER_ID = 1347987555177467914  # ← あなたのDiscordユーザーIDに置き換えること！

# --- 必要なimport ---
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput

# --- モーダル（フォーム） ---
class FeatureRequestModal(Modal, title="機能リクエストフォーム"):
    feature = TextInput(
        label="欲しい機能",
        placeholder="例: 音楽再生機能を追加してほしい",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        developer = await interaction.client.fetch_user(DEVELOPER_ID)
        embed = discord.Embed(
            title="📩 新しい機能リクエストが届きました",
            description=f"**送信者：** {interaction.user.mention}\n\n**リクエスト内容：**\n{self.feature.value}",
            color=discord.Color.green()
        )
        try:
            await developer.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ 開発者へのDMに失敗しました。", ephemeral=True)
            return
        await interaction.response.send_message("✅ ご要望を送信しました！", ephemeral=True)

# --- ボタン ---
class FeatureRequestButton(Button):
    def __init__(self):
        super().__init__(label="📬 機能をリクエストする", style=discord.ButtonStyle.primary, custom_id="feature_request")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FeatureRequestModal())

# --- View（ボタンの表示用） ---
class FeatureRequestView(View):
    def __init__(self):
        super().__init__(timeout=None)  # 永続化
        self.add_item(FeatureRequestButton())
        
# --- スラッシュコマンド ---
@bot.tree.command(name="request", description="Botに欲しい機能をリクエストできます")
async def request_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💡 機能リクエスト",
        description="Botに追加してほしい機能があれば、下のボタンからリクエストしてください！",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=FeatureRequestView())
bot.run(TOKEN)
