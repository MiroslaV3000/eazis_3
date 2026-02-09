import re

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import string
from typing import Dict, List, Tuple, Union

import requests
from bs4 import BeautifulSoup

# Загрузка необходимых ресурсов NLTK (если они еще не установлены)

nltk.data.find('tokenizers/punkt')
nltk.data.find('corpora/stopwords')


class SentenceExtraction:
    """
    Класс SentenceExtraction для автоматического реферирования документов
    методом Sentence Extraction.

    Создает реферат, состоящий из классического реферата и реферата
    в виде списка ключевых слов. Поддерживает английский (en) и испанский (es).
    """

    def __init__(self, keyword_count: int = 15):
        self.keyword_count = keyword_count  # Размер списка ключевых слов остается в конструкторе
        self.stop_words = {
            'en': set(stopwords.words('english')),
            'es': set(stopwords.words('spanish'))
        }
    @staticmethod
    def clean_text(text):
        # Убираем HTML entities
        text = re.sub(r'&[^;]+;', ' ', text)
        # Заменяем все пробельные символы на один пробел
        text = re.sub(r'\s+', ' ', text)
        # Убираем пробелы в начале и конце
        text = text.strip()
        return text

    def _detect_language(self, text: str) -> str:
        """
        Эвристика для определения языка (English или Spanish).
        """
        text_lower = text.lower()
        tokens = word_tokenize(text_lower, language='english')

        en_stop_words = self.stop_words['en']
        es_stop_words = self.stop_words['es']

        en_count = sum(1 for token in tokens if token in en_stop_words)
        es_count = sum(1 for token in tokens if token in es_stop_words)

        if es_count > en_count:
            return 'es'
        else:
            return 'en'

    def _preprocess_document(self, text: str, lang: str) -> Tuple[List[str], List[str], Dict[str, float]]:
        """
        Предварительная обработка документа: токенизация, фильтрация и вычисление весов слов (TF).
        """
        sentences = sent_tokenize(text, language='english' if lang == 'en' else 'spanish')

        word_tokens_all = []
        for sentence in sentences:
            words = word_tokenize(sentence, language='english' if lang == 'en' else 'spanish')

            filtered_words = [
                word.lower()
                for word in words
                if word.lower() not in self.stop_words[lang]
                   and word not in string.punctuation
                   and word.isalpha()
            ]
            word_tokens_all.extend(filtered_words)

        word_freq = Counter(word_tokens_all)
        max_freq = max(word_freq.values()) if word_freq else 1

        word_weights = {
            word: freq / max_freq for word, freq in word_freq.items()
        }

        return sentences, word_tokens_all, word_weights

    def _calculate_sentence_weights(self, sentences: List[str], word_weights: Dict[str, float], lang: str) -> List[Tuple[str, float, int]]:
        """
        Вычисление весов предложений.
        """
        scored_sentences = []

        for i, sentence in enumerate(sentences):
            words = word_tokenize(sentence, language='english' if lang == 'en' else 'spanish')
            sentence_word_freq = Counter(word.lower() for word in words if word.isalpha())

            score_z = 0.0

            for word, tf_si in sentence_word_freq.items():
                normalized_tf_si = tf_si / len(words) if words else 0
                word_weight = word_weights.get(word, 0.0)
                score_z += normalized_tf_si * word_weight


            posd_score = 1 - (i / len(sentences))
            posp_score = 1.0

            final_weight = score_z * posd_score * posp_score

            scored_sentences.append((sentence, final_weight, i))
        print(scored_sentences)
        return scored_sentences

    def _generate_classic_abstract(self, scored_sentences: List[Tuple[str, float, int]], abstract_size: int) -> str:
        """
        Генерация классического реферата: использует переданный abstract_size.
        """
        # Сортировка по весу (убывающему) и выбор N лучших, где N = abstract_size
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:abstract_size]

        # Сортировка выбранных предложений по исходному индексу для сохранения порядка
        ordered_abstract = sorted(top_sentences, key=lambda x: x[2])

        # Сборка реферата
        abstract = " ".join([s[0] for s in ordered_abstract])

        return abstract

    def _generate_keyword_abstract(self, word_weights: Dict[str, float]) -> List[str]:
        """
        Генерация реферата в виде списка ключевых слов.
        """
        sorted_keywords = sorted(word_weights.items(), key=lambda item: item[1], reverse=True)
        # Использует self.keyword_count из конструктора
        keyword_list = [word for word, weight in sorted_keywords[:self.keyword_count]]

        return keyword_list

    def create_abstract(self, url: str, abstract_size: int = 10) -> Dict[str, Union[str, List[str]]]:
        site = requests.get(url)
        site_html = BeautifulSoup(site.content, 'html.parser')

        # Найти все теги <p>
        paragraphs = site_html.find_all('p')

        # Собрать все предложения
        all_sentences = []
        for p in paragraphs:
            text = p.get_text().strip()
            if text:
                # Разделить текст на предложения
                sentences = re.split(r'[.!?]+', text)
                # Отфильтровать пустые и слишком короткие "предложения"
                valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
                all_sentences.extend(valid_sentences)

        text = '. '.join(all_sentences)
        text = self.clean_text(text)

        # 1. Определение языка
        lang = self._detect_language(text)
        print(f"Обнаружен язык: {lang} ({'English' if lang == 'en' else 'Spanish'})")

        # 2. Предварительная обработка
        sentences, all_words, word_weights = self._preprocess_document(text, lang)

        if not sentences or not word_weights:
            return {
                "классический реферат": "Не удалось обработать текст или он слишком короткий.",
                "реферат в виде списка ключевых слов": []
            }

        # 3. Расчет весов предложений
        scored_sentences = self._calculate_sentence_weights(sentences, word_weights, lang)

        # 4. Генерация классического реферата (Использует переданный abstract_size)
        classic_abstract = self._generate_classic_abstract(scored_sentences, abstract_size)

        # 5. Генерация реферата в виде списка ключевых слов
        keyword_abstract = self._generate_keyword_abstract(word_weights)
        return {
            "classic_abstract": classic_abstract,
            "keyword_abstract": keyword_abstract
        }

