import re

from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup

load_dotenv()

class NeuralNetwork:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OP_KEY"),
        )

    @staticmethod
    def clean_text(text):
        # Убираем HTML entities
        text = re.sub(r'&[^;]+;', ' ', text)
        # Заменяем все пробельные символы на один пробел
        text = re.sub(r'\s+', ' ', text)
        # Убираем пробелы в начале и конце
        text = text.strip()
        return text


    def search(self,question: str, context: str,) -> dict:
        completion = self.client.chat.completions.create(
          extra_headers={},
          extra_body={},
          model="nvidia/nemotron-nano-9b-v2:free",
          messages=[
            {
              "role": "user",
              "content": [
                  {
                      "type": "text",
                      "text": question
                  },
                  {
                      "type": "text",
                      "text": context
                  },
              ]
            }
          ]
        )
        return completion.choices[0].message.content

    def create_abstract(self, url: str, abstract_size: int = 10):
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
        question = f"Write an abstract of the text which will consist of only so many: {abstract_size} sentences of the text, the abstract must be written in the same language as the original text."
        classic_abstract = self.search(question=question, context=text)
        question = f"Write a summary of the text, which will consist only of a list of the most key words in the text and nothing more. Example: *word\n *word\n *word\n."
        keyword_abstract = self.search(question=question, context=text)
        return {
            "classic_abstract": classic_abstract,
            "keyword_abstract": keyword_abstract
        }
