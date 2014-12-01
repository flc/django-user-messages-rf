from django.utils.translation import ugettext_lazy as _

from rest_framework import generics
from rest_framework import viewsets, views
from rest_framework import mixins
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework import exceptions
from rest_framework import status
from rest_framework import filters

from user_messages.models import Thread, Message

from .serializers import ThreadSerializer, CreateThreadSerializer, MessageSerializer
from .permissions import ThreadPermission


class LatestMessageAtFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        params = request.QUERY_PARAMS
        if 'latest_message_at__lt' in params:
            return queryset.filter(latest_message_at__lt=params['latest_message_at__lt'])
        return queryset


class ThreadViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
    ):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, LatestMessageAtFilterBackend)
    # paginate_by = 100

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateThreadSerializer
        return super(ThreadViewSet, self).get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset.filter(users__id=user.id)
        if self.request.method == "GET":
            try:
                qs = qs.prefetch_related("users__profile")
            except AttributeError:
                # in case of there is no profile relation
                qs = qs.prefetch_related("users")
            qs = qs.order_by("-latest_message_at")
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            self.pre_save(serializer.object)
            thread = serializer.save(from_user=request.user)
            data = ThreadSerializer(thread).data
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageListView(generics.ListCreateAPIView):
    queryset = Message.objects.all()
    permission_classes = (IsAuthenticated, ThreadPermission)
    serializer_class = MessageSerializer

    def get_queryset(self):
        thread_pk = self.kwargs['thread_pk']
        return self.queryset.filter(thread=thread_pk)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            self.pre_save(serializer.object)

            # self.object = serializer.save(force_insert=True)
            thread = Thread.objects.get(id=self.kwargs['thread_pk'])
            from_user = request.user
            self.object = Message.objects.new_reply(thread, from_user, serializer.data['content'])

            data = self.get_serializer(self.object).data
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
