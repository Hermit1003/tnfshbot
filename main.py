import asyncio
from functools import partial
import aiohttp
from bs4 import BeautifulSoup
import discord
import constants
import requests
import json
from discord.ext import commands

# 設定 intents
intents = discord.Intents.default()
intents.message_content = True

# 設定網站 URL
URL = 'https://www.tnfsh.tn.edu.tw/latestevent/index.aspx?Parser=9,3,19'

# 設定定時更新的時間間隔（單位為秒）
UPDATE_INTERVAL = 3600  # 每小時更新一次

# 建立 Bot 實例，指定自訂的指令前綴詞
bot = commands.Bot(command_prefix='t!', intents=intents)

#讀取文字json，以便後續使用
txt_url = "https://raw.githubusercontent.com/Hermit1003/tnfshbot/main/txt.json"
# 發送 GET 請求取得 JSON 檔案的內容
txt_response = requests.get(txt_url)
# 檢查請求是否成功(200成功)
if txt_response.status_code == 200:
    # 使用 json.loads() 函數解析 JSON 檔案的內容為 Python 字典物件
    txt = json.loads(txt_response.text)

#讀取json，輸出command list
async def command_list(ctx):
    # 指定 JSON 檔案的網址
    json_url = "https://raw.githubusercontent.com/Hermit1003/tnfshbot/main/command_list.json"

    # 發送 GET 請求取得 JSON 檔案的內容
    response = requests.get(json_url)

    # 檢查請求是否成功(200成功)
    if response.status_code == 200:
        # 使用 json.loads() 函數解析 JSON 檔案的內容為 Python 字典物件
        command_list = json.loads(response.text)
        # 現在 command_list 變數中就包含了 JSON 檔案的內容，可以直接使用
        await ctx.reply(f"> **info**:{command_list['info']}\n> **command**:{command_list['command']}\n> **news**:{command_list['news']}\n{command_list['tip']}", mention_author=False)
    else:
        print("無法取得 JSON 檔案，錯誤碼:", response.status_code)

#DM用戶公告詳情
async def show_details(url: str, title: str, interaction: discord.Interaction):
    user = interaction.user
    try:
        await user.send(f"已釘選公告: {url}")
        if "置頂" in title:
            title = title[:2] + title[4:]
        await interaction.response.send_message(f"*已釘選消息({title})，請至您的私人訊息查看。*", ephemeral=True)
    except discord.Forbidden:
        # 如果用戶關閉了私人訊息，將無法發送訊息
        await interaction.response.send_message("*由於您關閉了私人訊息，我無法傳送訊息給您，請開啟後再試試吧！*", ephemeral=True)
    except Exception as e:
        # 其他異常情況
        await interaction.response.send_message(f"*發生錯誤，請回報錯誤資訊給相關人員: {str(e)}*", ephemeral=True)


# 定義更新公告的函式
async def update_announcement(ctx, f: int, l: int):
    # 發送 HTTP GET 請求取得網頁內容
    print('Sending HTTP GET request...')
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            html = await response.text(encoding='utf-8')

    # 使用 BeautifulSoup 解析 HTML 文件
    print('Parsing HTML...')
    soup = BeautifulSoup(html, 'html.parser')

    # 找到所有的表格元素
    ul = soup.find("ul", class_="list list_type")

    if not ul:
        raise ValueError("找不到目標元素")

    # 找到每一個項目
    items = ul.find_all("li")

    # 發送訊息到指定聊天頻道
    print('Sending message to Discord channel...')

    # 以下修改為只顯示前五則
    for i, item in enumerate(items[f:l]):
        message = item.get_text().strip()
        url = item.find("a")["href"]
        url = f"https://www.tnfsh.tn.edu.tw/latestevent/{url}"
        if not message:
            print("Announcement message is empty, skipping...")
        else:
            message_lines = message.split('\n')
            message_lines[0] = "**" + message_lines[0] + "**"
            message_lines[1] = "發布單位: " + message_lines[1]
            message_lines[2] = "發布日期: " + message_lines[2]
            message = '\n'.join(message_lines)
            if "置頂" in message:
                message = f">>> {message[:2]}[{message[2:4]}]{message[4:]}"
            else:
                message = f">>> {message}"
            title = message_lines[0]
            view = discord.ui.View()
            button_go_to_announcement = discord.ui.Button(label="前往公告", url=f"{url}")
            view.add_item(button_go_to_announcement)

            button_show_details = discord.ui.Button(label="釘選至私人訊息", style=discord.ButtonStyle.primary)
            button_show_details.callback = partial(show_details, url, title)

            view.add_item(button_show_details)

            await ctx.send(message, view=view, mention_author=False)


# 當 Discord bot 客戶端啟動時執行
@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))

    # 每隔指定的時間更新一次公告
    while True:
        print('Updating announcement...')
        #await update_announcement()
        await asyncio.sleep(UPDATE_INTERVAL)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        # 捕獲參數解析錯誤
        await ctx.author.send(txt["txt"][0])#("參數格式錯誤，請重新檢查。")
        return
    raise error  # 如果不是參數解析錯誤，則重新拋出異常

@bot.command()
async def info(ctx):
    # 檢查訊息的來源頻道是否為指定的頻道
    if ctx.channel != bot.get_channel(constants.DISCORD_CHANNEL_ID):
        await ctx.author.send(txt["txt"][1])#("此指令僅能在指定的頻道內使用。")
        return
    # 顯示指令列表
    await ctx.reply(txt["txt"][2], mention_author=False)#("請在頻道發送 `t!command` 來獲取指令列表。")

@bot.command()
async def news(ctx, l: int = 10):
    # 檢查訊息的來源頻道是否為指定的頻道
    if ctx.channel != bot.get_channel(constants.DISCORD_CHANNEL_ID):
        await ctx.author.send(txt["txt"][1])#("此指令僅能在指定的頻道內使用。")
        return
    # 手動觸發公告更新
    print('Updating announcement...')
    if 1 <= l <= 18:
        await update_announcement(ctx, 1, l + 1)
    else:
        await ctx.reply(txt["txt"][3], mention_author=False)#("由於技術限制，目前僅提供查看20條消息，請將參數設定在1至20之間。")

@bot.command()
async def command(ctx):
    # 檢查訊息的來源頻道是否為指定的頻道
    if ctx.channel != bot.get_channel(constants.DISCORD_CHANNEL_ID):
        await ctx.author.send(txt["txt"][1])#("此指令僅能在指定的頻道內使用。")
        return
    #顯示指令列表
    await command_list(ctx)

@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    # 關閉機器人(僅允許服主使用)
    exit()

# 禁用 t!help 指令
bot.remove_command('help')

# 啟動 Discord Bot
bot.run(constants.DISCORD_TOKEN)
