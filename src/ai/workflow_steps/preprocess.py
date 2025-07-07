# Standard library imports
import logging
import re

# External library imports
import pandas as pd
import pymorphy3
from llama_index.core.workflow import StartEvent

# Internal module imports
from ..workflow_events import PreprocessEvent


# Configure module-level logging
logger = logging.getLogger(__name__)

# Initialize morphological analyzer
morphological_analyzer = pymorphy3.MorphAnalyzer()


def normalize_whitespace(text: str) -> str:
    """Remove excessive whitespace and normalize spacing in text.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    words = text.split()
    normalized_words = [word.strip() for word in words]
    return ' '.join(normalized_words)


def preprocess_query_text(text: str) -> str:
    """Preprocess and clean query text for better matching.
    
    This function performs comprehensive text preprocessing including:
    - Greeting and polite words removal
    - Email, link, and phone number anonymization
    - Glossary expansion for abbreviations
    - Morphological analysis for word normalization
    - Profanity and role-specific terms filtering
    
    Args:
        text: Raw input text to preprocess
        
    Returns:
        Cleaned and processed text ready for retrieval
    """
    logger.info(f"Starting text preprocessing for query: {text[:50]}...")
    
    greeting_words = {
        'здравствуйте', "здравствуй", 'привет', "приветствую", 'добрый', 
        'день', 'утро', 'вечер', "ночь", "дд"
    }

    polite_words = {
        'пожалуйста', 'пож', 'будь', 'добрый', 'спасибо', 'благодарю', 
        'прошу', "спс", "плиз", "плз"
    }

    self_intro_words = {
        'я', 'меня', 'зовут', 'будучи', 'являюсь'
    }

    quest_words = {
        "как", "где", "какой"
    }

    request_verbs = {
        'хотеть', 'просить', 'помогать', 'надо', 'нужно', 'требовать', 
        'просьба', 'возможность', "необходимо", "подсказать"
    }
    
    roles = {
        "bp", 'менеджер', 'руководитель', 'работник',
        'начальник', 'администратор', "должность"
    }
    
    profanity = {
        'блять', "бля", "сука", "пиздец", "хуй", "нахуй", "хрен", "нахрен", 
        "хуйня", "пизда", "ебать", "ебанина", "заебал", "заебало"
    }

    # Regex patterns for anonymization
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    link_pattern = r'(https?://[^\s]+|www\.[^\s]+)'

    # Initial text normalization
    text = text.lower().strip()
    text = re.sub(email_pattern, 'MAIL', text)
    text = re.sub(link_pattern, 'LINK', text)
    text = re.sub(r'\+7 \(xxx\) xxx xx xx', 'PHONE', text)
    text = re.sub(r'табельный номер \d+', '', text)
    text = re.sub(r'тн \d+', '', text)
    text = re.sub(r'№ \d+', '', text)
    text = normalize_whitespace(text)

    # Glossary for abbreviation expansion
    glossary_dict = {
        'лк': 'личный кабинет',
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
        "пб": "платежная база",
        "сф": "система финансов",
        "трв": "табель рабочего времени",
        "есп": "единая система приемки",
        "рц": "распределительный центр",
        "бс": "больничный лист",
        "скд": "система корпоративных документов",
        "sap": "корпоративная система для управления ресурсами и бизнес-процессами",
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

    # Apply glossary expansion
    for abbreviation, full_form in glossary_dict.items():
        pattern = r'\b' + re.escape(abbreviation) + r'\b'
        text = re.sub(pattern, full_form, text, flags=re.IGNORECASE)

    # Tokenize and filter tokens
    tokens = []
    for sentence in re.split(r'[.,!?;:()\[\]{}/-]', text.lower()):
        tokens.extend(sentence.split())
        
    tokens_to_remove = []
    for token in tokens:
        normalized_word = morphological_analyzer.parse(token)[0].normal_form
        
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
    
    processed_text = filtered_text.strip()
    logger.info(f"Text preprocessing completed. Original length: {len(text)}, "
                f"Processed length: {len(processed_text)}")
    
    return processed_text


async def preprocess_step(ev: StartEvent) -> PreprocessEvent:
    """Execute the preprocessing step for the workflow.
    
    Args:
        ev: StartEvent containing the original user query
        
    Returns:
        PreprocessEvent containing the cleaned query
    """
    query = ev.query
    logger.info(f"Starting preprocessing step for query: {query[:50]}...")
    
    query_clean = preprocess_query_text(query)
    
    logger.info("Preprocessing step completed successfully")
    return PreprocessEvent(query_clean=query_clean)
