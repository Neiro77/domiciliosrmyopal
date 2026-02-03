from models import db, Notification

def notify(user_id, message):
    notif = Notification(
        user_id=user_id,
        message=message
    )
    db.session.add(notif)
    db.session.commit()
