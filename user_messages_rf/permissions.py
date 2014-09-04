from django.core.exceptions import ObjectDoesNotExist

from rest_framework import permissions

from user_messages.models import Thread


class ThreadPermission(permissions.BasePermission):

    def _get_object(self, request, view):
        if not hasattr(self, "_thread_cache"):
            pk = view.kwargs['thread_pk']
            try:
                obj = Thread.objects.get(pk=pk)
            except Thread.DoesNotExist:
                obj = None
            self._thread_cache = obj
        return self._thread_cache

    def has_permission(self, request, view):
        obj = self._get_object(request, view)
        if not obj:
            return False
        # is the user a participant in the thread?
        return obj.users.filter(pk=request.user.pk).exists()
