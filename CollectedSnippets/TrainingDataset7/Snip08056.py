def get_session_store_class(cls):
        from django.contrib.sessions.backends.db import SessionStore

        return SessionStore