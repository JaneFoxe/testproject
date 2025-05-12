from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl
import string
import random
import json
import os

app = FastAPI()

DATA_FILE = "urls.json"


class URLRequest(BaseModel):
    url: HttpUrl


def load_data():
    """
    Метод пытается загрузить данные из json-файла
    :return: Словарь с данными из JSON-файла, или пустой словарь в случае ошибки или отсутствия файла
    """
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_data(data):
    """
    Сохраняет данные в json-файл, указанный в переменной 'DATA_FILE'
    :param data: Данные, которые необходимо сохранить, dict или list
    :return: None
    """
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_short_id(length=8):
    """
    Метод, который генерирует строку из случайных букв и цифр
    :param length:Длина строки. По умолчанию 8
    :return: случайная строка заданной длины - 8 знаков
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


@app.get("/", response_class=HTMLResponse)
async def show_form():
    """
    Обрабатывает get-запрос на корневой маршрут и возвращает html-форму для сокращения ссылок
    :return:
    """
    return """
    <html>
      <head>
        <title>Сократитель ссылок</title>
      </head>
      <body>
        <h2>Сократить ссылку</h2>
        <form action="/shorten" method="post">
          <input type="text" name="url" placeholder="https://example.com" size="50" required />
          <button type="submit">Сократить</button>
        </form>
      </body>
    </html>
    """


@app.post("/shorten", response_class=HTMLResponse)
async def handle_form(url: str = Form(...)):
    """
    Обрабатывает post-запрос с формы и создаёт сокращённую ссылку.

    Принимает url из формы, проверяет, существует ли уже его сокращённая версия. Если существует — возвращает её.
    Если нет — генерирует уникальный идентификатор, сохраняет его вместе с оригинальной ссылкой в файл, и возвращает
    html-страницу с готовой сокращённой ссылкой.

    :param url: Оригинальный url, отправленный через html-форму
    :return: html страница с сокращенной версией ссылки
    """
    data = load_data()
    # Проверка на дубликаты
    for key, val in data.items():
        if val == url:
            short_id = key
            break
    else:
        short_id = generate_short_id()
        while short_id in data:
            short_id = generate_short_id()
        data[short_id] = url
        save_data(data)

    short_link = f"http://127.0.0.1:8000/{short_id}"
    return f"""
    <html>
      <body>
        <p>Ваша сокращённая ссылка:</p>
        <a href="{short_link}">{short_link}</a><br><br>
        <a href="/">Назад</a>
      </body>
    </html>
    """


@app.get("/{short_id}")
async def redirect_url(short_id: str):
    """
    Обрабатывает переход по сокращённой ссылке и перенаправляет на оригинальный url

    Ищет оригинальный url по переданному идентификатору. Если идентификатор найден — выполняет редирект
    Если не найден — возвращает ошибку 404.
    :param short_id: str
    :return: редирект на оригинальный url или выдает ошибку 404, если идентификатор не найден
    """
    data = load_data()
    original_url = data.get(short_id)
    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(url=original_url, status_code=307)
