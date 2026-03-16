import discord
import requests
from datetime import datetime, timedelta
import time
import aiohttp
import asyncio

TOKEN_BOT = TOKEN_BOT
CHANNEL_ID = CHANNEL_ID
CLIENT_ID = CLIENT_ID
CLIENT_SECRET = CLIENT_SECRET
TOKEN_URL = TOKEN_URL
API_URL = API_URL

#Si se quiere probar solicitud token en postman el client_secret es pw y client_id es usuario 
intents = discord.Intents.default()
client = discord.Client(intents=intents)
channel = client.get_channel(CHANNEL_ID)

class Token:
    def __init__(self):
        self.valor = None
        self.hora = None
    def update(self, valor):
       self.valor = valor
       self.hora = datetime.now()

async def lastMessageBot(channel, botUser):
    async for message in channel.history(limit=10):
        if message.author == botUser:
            return message
    return None

token = Token()
#print(f'Hora de token inicializado: {token.hora.strftime("%H:%M:%S")}')

async def reviewConditionsChatAndAPI():
  await client.wait_until_ready()

  while True:
    #print(f'Hora de consulta si ya paso 5 min, hora actual: {datetime.now().strftime("%H:%M:%S")}')
    if token.hora == None or datetime.now() >= token.hora + timedelta(minutes=55):
      try:
        responseToken = requests.post(
        TOKEN_URL,
        data={'grant_type': 'client_credentials'},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        auth=(CLIENT_ID, CLIENT_SECRET))

        responseToken.raise_for_status()
        access_token = responseToken.json().get('access_token')
        token.update(access_token)
        # print(f'Valor token: {token.valor}')
        # print(f'Valor hora: {token.hora}')
      except responseToken.exceptions.RequestException as errorToken:
          print(f'Error request: {errorToken}')  
          await asyncio.sleep(300)
          continue
      
      headers = {
          'Authorization': f'Bearer {access_token}',
          'Content-Type': 'application/json'
      }
      #Schema GraphQL WarcraftLogs https://es.warcraftlogs.com/v2-api-docs/warcraft/
      # Query GraphQL info Guild
      queryGuild = """
      {
        guildData {
          guild(name: "Vankers", serverSlug: "ragnaros", serverRegion: "US") {
            id
            name
          }
        }
      }
      """
      # Query GrapQL reports Guild
      queryReportGuild = """
      {
        reportData {
          reports(guildID: 609805, limit: 1){
            data {
              code
            }
          } 
        }
      }"""

      # try:
      #   responseAPIGuildId = requests.post(API_URL, headers=headers, json={'query': queryGuild})
      #   responseAPIGuildId.raise_for_status()
      # except responseAPIGuildId.exceptions.RequestException as errorGuild:
      #    print(f'Error request: {errorGuild}')


        
      try:
        responseAPIReportGuild = requests.post(API_URL, headers=headers, json={'query': queryReportGuild})
        responseAPIReportGuild.raise_for_status()
        dataReport = responseAPIReportGuild.json()
        reports = dataReport['data']['reportData']['reports']['data']
        reportCode = reports[0]['code']
        print(f'Link del warcraftlog: https://www.warcraftlogs.com/reports/{reportCode}')
      except responseAPIReportGuild.exceptions.RequestException as errorReport:
        print(f'Error request: {errorReport}')
        await asyncio.sleep(300)
        continue
      
      lastMessage = None
      lastMessageChatBot = await lastMessageBot(client.get_channel(CHANNEL_ID), client.user)

      if lastMessageChatBot:
            if "/reports/" in lastMessageChatBot.content:
                lastMessage = lastMessageChatBot.content.split("/reports/")[1].split()[0]

      # async def reviewMessage():
      #   lastMessageChatBot = await lastMessageChatBot(client.get_channel(CHANNEL_ID), client.user)
      #   lastCodeBot = lastMessageChatBot.split('/reports/')[1]

      # lastCodeBot = reviewMessage()

      # if lastCodeBot != reportCode or lastCodeBot == None:
      #   print(f'Nuevo codigo de reporte: {reportCode}')
      if lastMessage != reportCode:
        link = f"https://www.warcraftlogs.com/reports/{reportCode}"
        await client.get_channel(CHANNEL_ID).send(link)
        print(f"Se publicó nuevo reporte: {link}")
      else:
        print("Mismo reporte, no se publica.")
        await asyncio.sleep(300)
      # time.sleep(300)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    client.loop.create_task(reviewConditionsChatAndAPI())

client.run(TOKEN_BOT)
