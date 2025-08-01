"""
Script for preprocessing text data in a dataset

This script provides functions to preprocess text, including:
- Lowercasing and stripping whitespace
- Replacing emails, links, and phone numbers with placeholders
- Removing extra spaces inside the text
- Expanding glossary abbreviations to full forms
- Removing greetings, polite words, self-introductions, question words, request verbs, profanity, and role-related words
- Tokenizing and normalizing words using pymorphy3

Dependencies:
- pandas
- pymorphy3

Usage:
    Import and use the preprocess(text) function in your data pipeline.
"""

import re

import pandas as pd
import pymorphy3


morph = pymorphy3.MorphAnalyzer()


def clear_spaces_inside(text):
    words = text.split()
    words = list(map(lambda x: x.strip(), words))
    text_clear = ' '.join(words)

    return text_clear


def preprocess(text):
  
    greeting_words = {
        'здравствуйте', "здравствуй", 'привет', "приветствую", 'добрый', 'день', 'утро', 'вечер', "ночь", "дд"
    }

    polite_words = {
        'пожалуйста', 'пож', 'будь', 'добрый', 'спасибо', 'благодарю', 'прошу', "спс", "плиз", "плз"
    }

    self_intro_words = {
        'я', 'меня', 'зовут', 'будучи', 'являюсь'
    }

    quest_words = {
        "как", "где", "какой"
    }

    request_verbs = {
        'хотеть', 'просить', 'помогать', 'надо', 'нужно', 'требовать', 'просьба', 'возможность', "необходимо", "подсказать"
    }
    roles = {
        "bp", 'менеджер', 'руководитель', 'работник',
        'начальник', 'администратор', "должность"
    }
    profanity = {
                'блять', "бля", "сука", "пиздец", "хуй", "нахуй", "хрен", "нахрен", "хуйня", "пизда", "ебать", "ебанина", "заебал", "заебало"
    }

    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    link_pattern = r'(https?://[^\s]+|www\.[^\s]+)'

    text = text.lower().strip()
    text = re.sub(email_pattern, 'MAIL', text)
    text = re.sub(link_pattern, 'LINK', text)
    text = re.sub('\+7 \(xxx\) xxx xx xx', 'PHONE', text)
    text = re.sub(r'табельный номер \d+', '', text)
    text = re.sub(r'тн \d+', '', text)
    text = re.sub(r'№ \d+', '', text)
    text = clear_spaces_inside(text)

    glossary_dict = {'лк': 'личный кабинет',
    'бир': 'беременность и роды',
    'зп': 'заработная плата',
    'ндфл': 'налог на доходы физических лиц',
    'стд': 'срочный трудовой договор',
    'тк': 'трудовой договор',
    'ао': 'авансовый отчет',
    'sla': 'сроки',
    'эцп': 'электронная цифровая подпись',
    'кр': 'кадровый резерв',
    "сфр": "социальный фонд россии",
    "мчд": "машиночитаемая доверенность",
    "дк": "директор кластера",
    "тел": "телефон",
    "адм": "административный кадровый резерв",
    "мс": "мастер-система",
    "орг": "организационная структура",
    "дмп": "директор магазина по продажам",
    "комп": "компьютер",
    "атз": "администратор торгового зала",
    "дм": "директор магазина",
    "мп": "мобильное приложение",
    "уз": "учетная запись",
    "кр": "кадровый резерв",
    "чаэс": "чернобыльская атомная электростанция",
    "мкс": "местность, приравненная к районам крайнего севера",
    "ркс": "район крайнего севера",
    "нрд": "ненормированный рабочий день",
    "доп": "дополнительный",
    "гос": "государственный",
    "lk": "личный кабинет",
    "бл": "больничный лист",
    "ду": "дежурный управляющий",
    "лтз": "администратор торгового зала",
    "атз": "администратор торгового зала",
    "тех": "технический",
    "сот": "система оценок труда",
    "асуз": "автоматизированная система учёта и записи",
    "скилаз": "система для автоматизации найма и развития талантов",
    "skillz": "система для автоматизации найма и развития талантов",
    "скиллаз": "система для автоматизации найма и развития талантов",
    "skillaz": "система для автоматизации найма и развития талантов",
    "здм": "заместитель директора магазина",
    "эп": "электронная подпись",
    "пк": "персональный консультант",
    "дк": "личный кабинет",
    "пб": "платежная база",
    "сф": "система финансов",
    "трв": "табель рабочего времени",
    "есп": "единая система приемки",
    "рц": "распределительный центр",
    "бс": "больничный лист",
    "скд": "система корпоративных документов",
    "sap": "корпоративная система для управления ресурсами и бизнес-процессами",
    "тк": "трудовой договор",
    "сб": "социальная безопасность",
    "атп": "автотранспортное предприятие",
    "ур": "удаленная работа",
    "дс": "дополнительное соглашение",
    "уд": "удаленный",
    "укэп": "усиленная квалифицированная электронная подпись",
    "унэп": "усиленная неквалифицированна электронная подпись",
    "фл": "физическое лицо",
    "юл": "юридическое лицо",
    "sed": "система электронного документооборота",
    "мед": "медицинский",
    "дмс": "добровольное медицинское страхование"
    }

    for key, value in glossary_dict.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        text = re.sub(pattern, value, text, flags=re.IGNORECASE)

    tokens = []
    for sent in re.split(r'[.,!?;:()\[\]{}/-]', text.lower()):
        tokens.extend(sent.split())
        
    tokens_to_remove = []
    for token in tokens:
        normalized_word = morph.parse(token)[0].normal_form
        if (normalized_word in greeting_words or
            normalized_word in polite_words or
            normalized_word in self_intro_words or
            normalized_word in quest_words or
            normalized_word in request_verbs or
            normalized_word in profanity or
            normalized_word in roles):
            tokens_to_remove.append(token)
    filtered_tokens = [token for token in tokens if token not in tokens_to_remove]
    filtered_text = ' '.join(filtered_tokens)
    filtered_text = re.sub(r'\s+', ' ', filtered_text)
    return filtered_text.strip()
