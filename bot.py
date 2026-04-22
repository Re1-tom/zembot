import discord
from discord.ext import commands, tasks
import random
import json
import os
import datetime
import pytz

JST = pytz.timezone('Asia/Tokyo')

# ここを、決められたチャンネルIDに置き換えてください
GOOD_MORNING_CHANNEL_ID = 1466034502160875612
ALLOWED_GACHA_CHANNEL_ID = 1493880361044672533  # ガチャ実行可能チャンネル
ALLOWED_OMIKUJI_CHANNEL_ID = 1485997367969976340  # おみくじ実行可能チャンネル
AUTO_ROLE_ID = 1481949665216954472  # 新規参加者に付与するロールIDに置き換えてください

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# 自動応答ルールの設定ファイル
RESPONSES_FILE = "auto_responses.json"
GACHA_DATA_FILE = "gacha.json"
OMIKUJI_DAILY_DATA_FILE = "omikuji_data.json"

# 自動モデレーション設定
NG_WORDS = ["badword1", "badword2", "spam", "inappropriate"]  # NGワードリスト（必要に応じて拡張）
SPAM_TIME_LIMIT = 5  # 秒単位：この時間以内のメッセージを連投とみなす
SPAM_MESSAGE_LIMIT = 2  # この回数以上のメッセージを連投とみなす

# ユーザーのメッセージ履歴（スパム検知用）
user_message_history = {}  # user_id: [timestamp1, timestamp2, ...]

# 自動応答ルールをメモリに読み込む
def load_responses():
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 自動応答ルールをファイルに保存
def save_responses(responses):
    with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)

# ガチャ回数データを読み込む
def load_gacha_data():
    if not os.path.exists(GACHA_DATA_FILE):
        return {}
    with open(GACHA_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ガチャ回数データを保存する
def save_gacha_data(data):
    with open(GACHA_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# おみくじの今日引いた記録を読み込む
def load_omikuji_daily_data():
    if not os.path.exists(OMIKUJI_DAILY_DATA_FILE):
        return {}
    with open(OMIKUJI_DAILY_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# おみくじの今日引いた記録を保存する
def save_omikuji_daily_data(data):
    with open(OMIKUJI_DAILY_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

auto_responses = load_responses()

rarities = {
    "大吉": ["やったね", "やるやん"],
    "中吉": ["良き", "ええやん", "なかなか"],
    "小吉": ["悪くはないか一旦", "まぁまぁ", "ちょっとラッキー"],
    "吉": ["普通やね", "まぁまぁ"],
    "凶": ["のびしろやで", "おつ","もう下がらないねラッキー（？）"],
    "末吉": ["まぁまぁ", "まぁ、人によるよね", "微妙なところ"],
    "半吉": ["半分のラッキーがあるさ", "中途半端やね", "まぁ、悪くはないかも"],
    "ぜむ吉": ["やほ、ぜむだよ", "なぁ…なぁ！"]
}

def pull():
    r = random.random()
    if r < 0.01:
        return "大吉"      # 1%
    elif r < 0.03:
        return "凶"        # 2%
    elif r < 0.08:
        return "ぜむ吉"    # 5%
    elif r < 0.18:
        return "中吉"      # 10%
    elif r < 0.35:
        return "半吉"      # 17%
    elif r < 0.60:
        return "吉"        # 25%
    elif r < 0.85:
        return "小吉"      # 25%
    else:
        return "末吉"      # 15%

@bot.command()
async def gacha(ctx):
    if ctx.channel.id != ALLOWED_GACHA_CHANNEL_ID:
        await ctx.send("このチャンネルでは使えません！")
        return

    data = load_gacha_data()
    user_id = str(ctx.author.id)

    if user_id not in data or data[user_id] <= 0:
        await ctx.send("ガチャ回数が残っていません！")
        return

    data[user_id] -= 1
    save_gacha_data(data)

    roll = random.random()
    if roll < 0.05:
        result = "🌟 SSR"
    elif roll < 0.20:
        result = "✨ SR"
    elif roll < 0.50:
        result = "🔵 R"
    else:
        result = "⚪ N"

    await ctx.send(
        f"{ctx.author.display_name} のガチャ結果：{result}\n残り回数：{data[user_id]}回"
    )

# おみくじ
@bot.command()
async def omikuji(ctx):
    if ctx.channel.id != ALLOWED_OMIKUJI_CHANNEL_ID:
        await ctx.send("このチャンネルでは使えません！")
        return

    data = load_omikuji_daily_data()
    user_id = str(ctx.author.id)
    today = datetime.datetime.now(JST).date().isoformat()

    if user_id in data and data[user_id] == today:
        await ctx.send("今日はもうおみくじ引いてるよ！また明日🎍")
        return

    result = pull()  # 確率に基づいた結果を取得
    comment = random.choice(rarities[result])  # コメントをランダムに選択
    data[user_id] = today
    save_omikuji_daily_data(data)

    await ctx.send(f"{ctx.author.mention} の結果は… **{result}**！ {comment}")

# 管理者：回数設定
@bot.command()
@commands.has_permissions(administrator=True)
async def setgacha(ctx, member: discord.Member, count: int):
    data = load_gacha_data()
    data[str(member.id)] = count
    save_gacha_data(data)

    await ctx.send(f"{member.display_name} のガチャ回数を {count} 回に設定しました！")

# 管理者：回数追加
@bot.command()
@commands.has_permissions(administrator=True)
async def addgacha(ctx, member: discord.Member, count: int):
    data = load_gacha_data()
    user_id = str(member.id)

    if user_id not in data:
        data[user_id] = 0

    data[user_id] += count
    save_gacha_data(data)

    await ctx.send(f"{member.display_name} に {count} 回追加しました！（現在：{data[user_id]}回）")

# 自分の残り回数確認
@bot.command()
async def gachacount(ctx):
    data = load_gacha_data()
    user_id = str(ctx.author.id)

    count = data.get(user_id, 0)
    await ctx.send(f"{ctx.author.display_name} の残り回数：{count}回")

# 自動応答関連のコマンド
@bot.command()
async def addresponse(ctx, *, args):
    """キーワードと応答を追加します。使用法: !addresponse <キーワード> -> <応答>"""
    if " -> " not in args:
        await ctx.send("❌ 形式が違います。\n使用法: `!addresponse <キーワード> -> <応答>`")
        return
    
    keyword, response = args.split(" -> ", 1)
    keyword = keyword.strip()
    response = response.strip()
    
    if not keyword or not response:
        await ctx.send("❌ キーワードと応答は両方入力してください。")
        return
    
    auto_responses[keyword] = response
    save_responses(auto_responses)
    await ctx.send(f"✅ **「{keyword}」** に対する応答を追加しました。\n応答: {response}")

@bot.command()
async def removeresponse(ctx, *, keyword):
    """キーワードの応答ルールを削除します。"""
    keyword = keyword.strip()
    
    if keyword not in auto_responses:
        await ctx.send(f"❌ **「{keyword}」** のルールが見つかりません。")
        return
    
    del auto_responses[keyword]
    save_responses(auto_responses)
    await ctx.send(f"✅ **「{keyword}」** のルールを削除しました。")

@bot.command()
async def listresponses(ctx):
    """現在の自動応答ルール一覧を表示します。"""
    if not auto_responses:
        await ctx.send("📋 まだ自動応答ルールが登録されていません。")
        return
    
    embed = discord.Embed(title="📋 自動応答ルール一覧", color=discord.Color.blue())
    for keyword, response in auto_responses.items():
        embed.add_field(name=f"🔑 {keyword}", value=response, inline=False)
    
    await ctx.send(embed=embed)

# メッセージイベント：自動応答の実行
@bot.event
async def on_message(message):
    # ボット自身のメッセージは反応しない
    if message.author == bot.user:
        await bot.process_commands(message)
        return
    
    # 自動モデレーション：NGワード検知
    message_content = message.content.lower()
    for ng_word in NG_WORDS:
        if ng_word.lower() in message_content:
            await message.delete()
            await message.channel.send(f"{message.author.mention} NGワードが検知されました。メッセージを削除しました。")
            return  # メッセージを削除したら、それ以上の処理をしない
    
    # 自動モデレーション：スパム・連投制限
    user_id = str(message.author.id)
    now = datetime.datetime.now(JST)
    
    if user_id not in user_message_history:
        user_message_history[user_id] = []
    
    # 古いメッセージを削除（時間制限外のものを）
    user_message_history[user_id] = [ts for ts in user_message_history[user_id] if (now - ts).seconds < SPAM_TIME_LIMIT]
    
    # 現在のメッセージを追加
    user_message_history[user_id].append(now)
    
    # 連投チェック
    if len(user_message_history[user_id]) > SPAM_MESSAGE_LIMIT:
        await message.delete()
        await message.channel.send(f"{message.author.mention} 連投が検知されました。メッセージを削除しました。")
        return  # メッセージを削除したら、それ以上の処理をしない
    
    # 登録されたキーワードをチェック
    for keyword, response in auto_responses.items():
        if keyword in message.content:
            await message.channel.send(response)
            break  # 最初にマッチしたキーワードのみ応答
    
    # コマンド処理を実行
    await bot.process_commands(message)

@tasks.loop(time=datetime.time(hour=22, minute=0, second=0))
async def good_morning_task():
    channel = bot.get_channel(GOOD_MORNING_CHANNEL_ID)
    if channel is None:
        print(f"[WARN] チャンネルID {GOOD_MORNING_CHANNEL_ID} が見つかりません。")
        return
    try:
        await channel.send("おはよう")
    except Exception as e:
        print(f"[ERROR] 朝の挨拶送信に失敗: {e}")

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        await member.add_roles(role)
        print(f"{member} に自動でロール {role.name} を付与しました。")
    else:
        print(f"ロールID {AUTO_ROLE_ID} が見つかりません。")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if not good_morning_task.is_running():
        good_morning_task.start()

import os
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("環境変数 DISCORD_BOT_TOKEN が設定されていません。トークンを設定してから再実行してください。")

bot.run(TOKEN)
