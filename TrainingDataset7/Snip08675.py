def get_connection(self, fail_silently=False):
        from django.core.mail import get_connection

        if not self.connection:
            self.connection = get_connection(fail_silently=fail_silently)
        return self.connection