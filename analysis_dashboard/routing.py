from channels.routing import ProtocolTypeRouter, URLRouter
from django_plotly_dash.routing import application as dpd_application

application = ProtocolTypeRouter({
    "http": dpd_application,
})