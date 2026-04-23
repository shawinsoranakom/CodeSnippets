def decode(self, session_data):
        try:
            return signing.loads(
                session_data, salt=self.key_salt, serializer=self.serializer
            )
        except signing.BadSignature:
            logger = logging.getLogger("django.security.SuspiciousSession")
            logger.warning("Session data corrupted")
        except Exception:
            # ValueError, unpickling exceptions. If any of these happen, just
            # return an empty dictionary (an empty session).
            pass
        return {}