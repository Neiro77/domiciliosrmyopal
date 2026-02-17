import threading
from flask import current_app

def send_email_async(app, msg):
    with app.app_context():
        try:
            from app import mail
            mail.send(msg)
            current_app.logger.info("Correo enviado correctamente.")
        except Exception as e:
            current_app.logger.error(f"Error enviando correo: {e}")


def send_async_email(msg):
    from flask import current_app
    app = current_app._get_current_object()
    thread = threading.Thread(target=send_email_async, args=(app, msg))
    thread.start()