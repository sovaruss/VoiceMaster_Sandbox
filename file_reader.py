import os
import docx
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

def read_pdf(file_path):
    """Извлечение текста из PDF"""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def read_docx(file_path):
    """Извлечение текста из DOCX"""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_epub(file_path):
    """Извлечение текста из EPUB"""
    book = epub.read_epub(file_path)
    text = ""
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text += soup.get_text() + "\n"
    return text

def get_text_from_file(file_path, extension):
    """Единая точка входа для всех типов файлов"""
    try:
        if extension == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif extension == 'pdf':
            return read_pdf(file_path)
        elif extension == 'docx':
            return read_docx(file_path)
        elif extension == 'epub':
            return read_epub(file_path)
        else:
            return None
    except Exception as e:
        print(f"Ошибка при чтении файла {extension}: {e}")
        return None