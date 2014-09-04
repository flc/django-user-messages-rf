from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework import fields

from user_messages.models import Thread, Message

from .helpers import get_user_serializer_class


class MessageSerializer(serializers.ModelSerializer):
    sender = get_user_serializer_class()(many=False, read_only=True)

    class Meta:
        model = Message
        fields = ("sender", "sent_at", "content", "thread")
        read_only_fields = ("sent_at", "thread")


class ThreadSerializer(serializers.ModelSerializer):
    users = get_user_serializer_class()(many=True, required=False)
    latest_message = MessageSerializer(source="latest_message", read_only=True)

    class Meta:
        model = Thread
        fields = ("id", "created", "users", "latest_message",)
        read_only_fields = ("id", "created",)


class CreateThreadSerializer(serializers.Serializer):
    to_users = serializers.SlugRelatedField(
        many=True,
        required=True,
        queryset=get_user_model().objects.filter(is_active=True),
        slug_field="username",
        )
    content = fields.CharField(required=True)

    def validate_to_users(self, attrs, source):
        to_users = attrs[source]

        if not to_users:
            raise serializers.ValidationError(
                "You have to specify at least one recipient."
                )

        request = self.context.get('request', None)
        sender = None
        if request:
            sender = request.user

        if sender and sender in to_users:
            raise serializers.ValidationError(
                "You can't start a conversation with yourself."
                )

        return attrs

    def save(self, **kwargs):
        obj = self.object
        from_user = kwargs.pop("from_user")
        msg = Message.objects.new_message(
            from_user=from_user,
            to_users=obj['to_users'],
            content=obj['content'],
            )
        return msg.thread



