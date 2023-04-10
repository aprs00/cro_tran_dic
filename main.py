import discord
import requests
import os
from bs4 import BeautifulSoup
# from googletrans import Translator
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv

intents = discord.Intents.all()
intents.members = True

client = discord.Client(intents=intents)

load_dotenv()

def get_definition_and_translation(word):
    # translator = Translator()
    translate_client = translate.Client()

    translation_response = translate_client.translate(word, target_language='hr')
    translation = translation_response['translatedText']

    if translation == word:
        return None, None, None, None, 'No translations found'
    
    definition, synonyms, example = scrape_word_definition(word)

    return definition, translation, synonyms, example, None

async def send_invalid_word(word, channel, error_message):
    msg = await channel.send(error_message)
    await word.delete(delay=5)
    await msg.delete(delay=5)

def format_response(word, translation, definition, example, synonyms):
    separator = '\n' + '-' * 53 + '\n'
    response = ''

    if translation:
        response = f'**{word}** - **{translation}**'
    if definition:
        response += f'\n{definition}'
    if synonyms:
        response += f'\n{synonyms}'
    if example:
        response += f'\n{example}'

    return response + separator

async def delete_all_channel_messages(channel):
    async for message in channel.history(limit=None):
        await message.delete()
    return

def scrape_word_definition(word): 
    url = f'https://www.vocabulary.com/dictionary/{word}'

    response = requests.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')
    print(soup)

    synonyms, example = None, None
    max_synonyms = 8

    definition_exists = soup.find('div', {'class': 'definition'})
    print(definition_exists)
    if not definition_exists:
        return None, None, None

    definition_div = soup.find('div', {'class': 'definition'})
    part_of_speech = definition_div.find('div', {'class': 'pos-icon'}).text.strip()
    definition = definition_div.text.replace(part_of_speech, '').strip()

    instances_div = soup.find('dl', {'class': 'instances'})
    instances_detail = instances_div.find('span', {'class': 'detail'})
    is_synonym = instances_detail.text.strip().lower() == 'synonyms:'
    if is_synonym:
        synonyms = ", ".join([s.text for s in instances_div.find_all('a')][:max_synonyms])

    example_div = soup.find('div', {'class': 'example'})
    if example_div:
        example = example_div.text.replace('\n', '')

    return definition, synonyms, example

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if str(message.channel.id) == os.getenv('DISCORD_CHANNEL_ID'):
        word = message.content

        if (word == '!delete-all'):
            await delete_all_channel_messages(message.channel)
            return

        definition, translation, synonyms, example, error_message = get_definition_and_translation(word)

        if error_message:
            return await send_invalid_word(message, message.channel, error_message)

        response = format_response(word, translation, definition, example, synonyms)

        await message.delete()
        await message.channel.send(response)

client.run(os.getenv('CROTRANDIC_BOT_ID'))
