import discord
from discord.ext import commands, tasks
import random
import json
import os
import datetime

# ここを、決められたチャンネルIDに置き換えてください
GOOD_MORNING_CHANNEL_ID = 1466034502160875612

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# 自動応答ルールの設定ファイル
RESPONSES_FILE = "auto_responses.json"

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

auto_responses = load_responses()

rarities = {
    "大吉": ["「やったね」", "やるやん"],
    "中吉": ["「良き」", "「まぁええやん」"],
    "小吉": ["「悪くはないか一旦」", "「まぁまぁ」"],
    "吉": ["「普通やね」", "「まぁまぁ」"],
    "凶": ["「のびしろやで」", "「おつ」"],
    "末吉": ["「後半に期待」", "「じわじわ来るタイプ」"],
    "半吉": ["「半分勝ちや」", "「惜しい！」"],
    "ぜむ吉": ["「やほ、ぜむだよ」", "「なぁ…なぁ！」"]
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
    rarity = pull()
    item = random.choice(rarities[rarity])
    await ctx.send(f"{rarity}！！ {item}を引いた！")

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
    
    # 登録されたキーワードをチェック
    for keyword, response in auto_responses.items():
        if keyword in message.content:
            await message.channel.send(response)
            break  # 最初にマッチしたキーワードのみ応答
    
    # コマンド処理を実行
    await bot.process_commands(message)

@tasks.loop(time=datetime.time(hour=7, minute=0, second=0))
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
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if not good_morning_task.is_running():
        good_morning_task.start()

import os
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("環境変数 DISCORD_BOT_TOKEN が設定されていません。トークンを設定してから再実行してください。")

bot.run(TOKEN)
