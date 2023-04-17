import asyncio
from functools import partial
import aiohttp
from bs4 import BeautifulSoup
import discord
import constants

intents = discord.Intents().all()
intents.message_content = True

# 設定網站 URL
URL = 'https://www.tnfsh.tn.edu.tw/latestevent/index.aspx?Parser=9,3,19'

# 設定定時更新的時間間隔（單位為秒）
UPDATE_INTERVAL = 3600  # 每小時更新一次

# 建立 Discord 客戶端
client = discord.Client(intents=intents)

#讀取json，輸出command list

async def command_list():
     return

#DM用戶公告詳情
async def show_details(url: str, interaction: discord.Interaction):
    user = interaction.user
    try:
        await user.send(f"已訂選公告: {url}")
    except discord.Forbidden:
        # 如果用戶關閉了私人訊息，將無法發送訊息
        await interaction.response.send_message("很遺憾的，您的私訊功能已關閉，我無法傳送訊息給您TAT")
    except Exception as e:
        # 其他異常情況
        await interaction.response.send_message(f"錯誤發生，請回報錯誤代碼給相關人員: {str(e)}")


# 定義更新公告的函式
async def update_announcement(f: int, l: int):
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

    # 取得指定聊天頻道的物件
    print('Getting Discord channel...')
    channel = client.get_channel(constants.DISCORD_CHANNEL_ID)

    print('Getting UserID...')


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
            view = discord.ui.View()
            button_go_to_announcement = discord.ui.Button(label="前往公告", url=f"{url}")
            view.add_item(button_go_to_announcement)

            button_show_details = discord.ui.Button(label="釘選至私人訊息", style=discord.ButtonStyle.primary)
            button_show_details.callback = partial(show_details, url)

            view.add_item(button_show_details)

            await channel.send(message, view=view)


# 當 Discord bot 客戶端啟動時執行
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

    # 每隔指定的時間更新一次公告
    while True:
        print('Updating announcement...')
        #await update_announcement()
        await asyncio.sleep(UPDATE_INTERVAL)

@client.event
async def on_message(message):
    if message.channel != client.get_channel(constants.DISCORD_CHANNEL_ID):
        return
    if message.author == client.user:
        return
    if message.content.startswith("t!"):
        usermsg = message.content.split("!")
        if usermsg[1] == "help":
            await message.channel.send("Please send `t!command` to check command list.")
        if usermsg[1] == "news":
            print('Updating announcement...')
            await update_announcement(1, 6)
        if usermsg[1] == "command":
            await command_list()#還在做，目前想讓他輸出線上json，這樣就不用塞文字進來了


# 啟動 Discord bot 客戶端
client.run(constants.DISCORD_TOKEN)
