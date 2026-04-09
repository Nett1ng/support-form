# config.py
import os

# Пытаемся импортировать dotenv только для локальной разработки
try:
    from dotenv import load_dotenv
    load_dotenv()  # Загружает .env только если файл существует
except ImportError:
    pass  # На Render dotenv не установлен, но это нормально

# Настройки почты
SMTP_SERVER = "smtp.yandex.com"
SMTP_PORT = 587
SMTP_LOGIN = "pirotimber@yandex.ru"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "ncvgofpvdwrjjpup")

# Секретный ключ для Flask
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key")

# Получатели по темам
TOPIC_RECIPIENTS = {
    "ЗП": "pirotimber@yandex.ru",
    "БМ": "pirotimber@yandex.ru",
    "Квартал": "pirotimber@yandex.ru",
    "ГФК": "pirotimber@yandex.ru",
    "Общая": "pirotimber@yandex.ru"
}

# Подкатегории для каждой темы
SUBCATEGORIES = {
    "ЗП": ["АЗК", "ФОТ", "КСП"],
    "БМ": ["Кредиты", "Кредитные карты", "Комиссионные продукты", 
           "Инвестиционные продукты", "Инвестиционные продукты УК", "Пассивные продукты"],
    "ГФК": ["Кредиты", "Кредитные карты", "Комиссионные продукты", 
            "Инвестиционные продукты", "Инвестиционные продукты УК", "Пассивные продукты"],
    "Квартал": [],
    "Общая": []
}

# Для темы "Квартал" - РОЛИ И ПОКАЗАТЕЛИ
ROLES = ['роль1', 'роль2', 'роль3']

INDICATORS_BY_ROLE = {
    "роль1": ["Показатель1", "Показатель2"],
    "роль2": ["Показатель3", "Показатель4"],
    "роль3": ["Показатель5", "Показатель6"]
}

PLAN_FACT = ["План", "Факт"]

# Настройки файлов
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}