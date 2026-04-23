def key_salt(self):
        return "django.contrib.sessions." + self.__class__.__qualname__