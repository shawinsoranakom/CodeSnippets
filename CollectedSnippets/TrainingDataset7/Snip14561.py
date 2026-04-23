def connection(self):
        return get_connection(backend=self.email_backend, fail_silently=True)