import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_notification(self, to_email, subject, text_body, html_body=None):
        # Создаём сообщение
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'Ваше приложение <{self.username}>'
        msg['To'] = to_email

        # Добавляем текстовую версию
        msg.attach(MIMEText(text_body, 'plain'))

        # Добавляем HTML версию, если есть
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        try:
            # Подключаемся к SMTP серверу
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Включаем шифрование
            server.login(self.username, self.password)

            # Отправляем письмо
            server.sendmail(self.username, to_email, msg.as_string())
            server.quit()

            print(f'Письмо отправлено на {to_email}')
            return {'success': True}
        except Exception as e:
            print(f'Ошибка отправки: {e}')
            return {'success': False, 'error': str(e)}



# Конфигурация для Gmail
email_service = EmailService(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    username='dmitrii.mironov.02.07@gmail.com',
    password='wcowvdsphgpsrvgs'
)

# Отправка уведомления
result = email_service.send_notification(
    to_email='dimastefanov2000@gmail.com',
    subject='Уведомление от приложения',
    text_body='Текст уведомления',
    html_body='<p>HTML версия уведомления</p>'
)
