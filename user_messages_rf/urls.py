from django.conf.urls import patterns, url, include

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'threads', views.ThreadViewSet)


urlpatterns = patterns('',
    url(r'', include(router.urls)),
    url(r'^threads/(?P<thread_pk>\d+)/messages/$',
        views.MessageListView.as_view(),
        name='message-list',
        ),
)
