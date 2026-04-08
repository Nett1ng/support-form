from flask import Flask, render_template, request, flash, redirect, url_for
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from config import (
    SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD,
    TOPIC_RECIPIENTS, SUBCATEGORIES, ROLES, INDICATORS_BY_ROLE, PLAN_FACT,
    MAX_FILE_SIZE, ALLOWED_EXTENSIONS
)

app = Flask(__name__)
app.secret_key = "super_secret_key"  # ВОЗВРАЩАЕМ ПРОСТОЙ КЛЮЧ


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def send_email(sender_email, subject, body, recipient, cc_email=None, attachments=None):
    msg = MIMEMultipart()
    msg['From'] = SMTP_LOGIN
    msg['To'] = recipient
    msg['Subject'] = subject
    
    if cc_email:
        msg['Cc'] = cc_email

    full_body = f"Обращение от сотрудника: {sender_email}\n\nОписание проблемы:\n{body}"
    msg.attach(MIMEText(full_body, 'plain'))

    # Прикрепляем файлы
    if attachments:
        for file_path, filename in attachments:
            try:
                with open(file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{filename}"'
                )
                msg.attach(part)
            except Exception as e:
                print(f"Ошибка прикрепления файла {filename}: {e}")

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        topic = request.form.get('topic')
        description = request.form.get('description')
        
        recipient = TOPIC_RECIPIENTS.get(topic)

        if not recipient:
            flash("Ошибка: Неверная тема обращения", "error")
            return redirect(url_for('index'))

        # Формируем тему в зависимости от выбранной категории
        if topic == "Квартал":
            # Для Квартал: Тема - Роль - Показатель - Тип
            role = request.form.get('role')
            indicator = request.form.get('indicator')
            plan_fact = request.form.get('plan_fact')
            
            if role and indicator and plan_fact:
                email_subject = f"{topic} - {role} - {indicator} - {plan_fact}"
            else:
                flash("Для темы 'Квартал' необходимо заполнить все поля", "error")
                return redirect(url_for('index'))
        else:
            # Для остальных тем: Тема - Подкатегория
            subcategory = request.form.get('subcategory')
            if subcategory:
                email_subject = f"{topic} - {subcategory}"
            else:
                email_subject = topic

        # Обработка загруженных файлов
        attachments = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    if file.content_length > MAX_FILE_SIZE:
                        flash(f"Файл {file.filename} слишком большой (макс. 10 МБ)", "error")
                        return redirect(url_for('index'))
                    
                    # Сохраняем файл временно
                    temp_path = os.path.join('/tmp', file.filename)
                    file.save(temp_path)
                    attachments.append((temp_path, file.filename))
                elif file.filename:
                    flash(f"Файл {file.filename} имеет недопустимый формат", "error")
                    return redirect(url_for('index'))

        try:
            if send_email(email, email_subject, description, recipient, cc_email=email, attachments=attachments):
                flash("Ваше обращение успешно отправлено! Копия отправлена вам на почту.", "success")
            else:
                flash("Ошибка при отправке письма. Попробуйте позже.", "error")
        finally:
            # Удаляем временные файлы
            for file_path, _ in attachments:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
        return redirect(url_for('index'))

    return render_template('index.html', 
                         topics=TOPIC_RECIPIENTS.keys(), 
                         subcategories=SUBCATEGORIES,
                         roles=ROLES,
                         indicators_by_role=INDICATORS_BY_ROLE,
                         plan_fact=PLAN_FACT)


if __name__ == '__main__':
    app.run(debug=True)