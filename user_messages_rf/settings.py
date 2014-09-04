from django.conf import settings


USER_SERIALIZER_CLASS = getattr(
    settings,
    'USER_MESSAGES_RF_USER_SERIALIZER_CLASS',
)
