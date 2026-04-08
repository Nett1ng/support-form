import os
import smtplib
import logging
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, request, jsonify

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
# Настройка логирования
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Конфигурация (берётся из переменных окружения Render)
# ─────────────────────────────────────────────────────────────
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)

def _send_email_task(to_email, subject, description, recipient, cc_email, attachments):
    """Внутренняя функция отправки. Вызывается в отдельном потоке."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        if cc_email:
            msg['Cc'] = cc_email

        msg.attach(MIMEText(description, 'plain', 'utf-8'))

        # Вложения (ожидается список путей к файлам)
        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(file_path)}"'
                        )
                        msg.attach(part)
                except Exception as e:
                    logger.warning(f"⚠️ Пропущено вложение {file_path}: {e}")

        logger.info(f"🔌 Подключение к {SMTP_SERVER}:{SMTP_PORT}...")
        
        # 🔑 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: явный timeout=10 секунд
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.starttls()

        server.login(SMTP_USER, SMTP_PASSWORD)
        
        recipients = [to_email]
        if cc_email:
            recipients.append(cc_email)

        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()
        logger.info(f"✅ Письмо успешно отправлено на {to_email}")

    except smtplib.SMTPConnectError as e:
        logger.error(f"❌ Ошибка подключения к SMTP (проверьте сервер/порт/файрвол): {e}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Ошибка логина/пароля SMTP: {e}")
    except TimeoutError:
        logger.error("❌ Таймаут подключения к SMTP-серверу")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка отправки: {e}")

@app.route("/", methods=["POST"])
def index():
    try:
        # Поддержка и JSON, и form-data
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()

        email = data.get("email")
        email_subject = data.get("email_subject", data.get("subject", "Без темы"))
        description = data.get("description", "")
        recipient = data.get("recipient", email)
        cc_email = data.get("cc_email", email)
        attachments = data.get("attachments", [])

        if not email:
            return jsonify({"status": "error", "message": "Поле 'email' обязательно"}), 400

        # 🚀 Запускаем отправку в фоне, чтобы Gunicorn не убивал воркер
        thread = threading.Thread(
            target=_send_email_task,
            args=(email, email_subject, description, recipient, cc_email, attachments),
            daemon=True
        )
        thread.start()

        logger.info(f"📤 Запрос принят. Отправка на {email} запущена в фоне.")
        return jsonify({
            "status": "accepted",
            "message": "Письмо принято в обработку"
        }), 202  # 202 Accepted — запрос принят, обработка идёт асинхронно

    except Exception as e:
        logger.exception("Ошибка при обработке HTTP-запроса")
        return jsonify({
            "status": "error",
            "message": "Внутренняя ошибка сервера"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)