def is_silenced(self):
        from django.conf import settings

        return self.id in settings.SILENCED_SYSTEM_CHECKS