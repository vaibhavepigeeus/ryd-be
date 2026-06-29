from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

from .models import Notification

logger = logging.getLogger(__name__)


def create_notification(*, user, title, message, action, templateID):
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        action=action,
        message_template=templateID,
    )

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "send_notification",
                "data": {
                    "id": notification.id,
                    "title": title,
                    "message": message,
                    "action": notification.action,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )
        notification.is_sent = True
        notification.save(update_fields=["is_sent"])
    except Exception as e:
        logger.error(f"WebSocket send failed: {e}")

    return notification
