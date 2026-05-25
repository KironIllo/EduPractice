import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

class EmailService:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def generate_verification_code(self):
        """Генерирует 6‑значный код подтверждения"""
        return str(random.randint(100000, 999999))

    def send_verification_code(self, to_email):
        """Отправляет код подтверждения на email"""
        code = self.generate_verification_code()
        print(code)
        subject = 'Код подтверждения регистрации'
        text_body = f'Ваш код подтверждения: {code}\n\nВведите его на странице регистрации.'
        html_body = f'''
        <html>
          <body>
            <h3>Код подтверждения регистрации</h3>
            <p>Ваш код: <strong>{code}</strong></p>
            <p>Введите его на странице регистрации.</p>
          </body>
        </html>
        '''

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'Ваше приложение <{self.username}>'
        msg['To'] = to_email

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.username, to_email, msg.as_string())
            server.quit()
            print(f'Код подтверждения отправлен на {to_email}')
            return {'success': True, 'code': code}
        except Exception as e:
            print(f'Ошибка отправки: {e}')
            return {'success': False, 'error': str(e)}
