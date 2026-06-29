from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import workflow.routing
from workflow.middleware import CookieKnoxAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": CookieKnoxAuthMiddleware(
        URLRouter(workflow.routing.websocket_urlpatterns)
    ),
})
