def exists(self, session_key):
        return self.model.objects.filter(session_key=session_key).exists()