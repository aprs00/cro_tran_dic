import discord
import requests
import os
from googletrans import Translator
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
intents.members = True

client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
CROTRANDIC_BOT_ID = os.getenv('CROTRANDIC_BOT_ID')

def get_definition_and_translation(word):
    translator = Translator()
    r = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')
    data = r.json()

    if isinstance(data, dict) and data.get('title', None) == 'No Definitions Found':
        return None, None, None, None, data['message']
    
    translation = translator.translate(word, dest='hr').text or None
    definition = data[0].get('meanings', [{}])[0].get('definitions', [{}])[0].get('definition', None)
    synonyms = data[0].get('meanings', [{}])[0].get('definitions', [{}])[0].get('synonyms', None)
    example = data[0].get('meanings', [{}])[0].get('definitions', [{}])[0].get('example', None)

    return definition, translation, synonyms, example, None

async def send_invalid_word(word, channel, error_message):
    msg = await channel.send(error_message)
    await word.delete(delay=5)
    await msg.delete(delay=5)

def format_response(word, translation, definition, synonyms, example):
    separator = '\n' + '-' * 50 + '\n'
    response = ''

    if translation:
        response = f'**{word}** - **{translation}**'
    if definition:
        response += f'\n{definition}'
    if synonyms:
        response += f'\n{", ".join(synonyms)}'
    if example:
        response += f'\n{example}'

    return response + separator

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if str(message.channel.id) == DISCORD_CHANNEL_ID:
        word = message.content
        definition, translation, synonyms, example, error_message = get_definition_and_translation(word)

        if error_message:
            return await send_invalid_word(message, message.channel, error_message)

        response = format_response(word, translation, definition, synonyms, example)

        await message.delete()
        await message.channel.send(response)

client.run(CROTRANDIC_BOT_ID)
