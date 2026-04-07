def handle_simple(cls, name):
        try:
            from django.conf import settings
        except ImportError:
            prefix = ""
        else:
            prefix = iri_to_uri(getattr(settings, name, ""))
        return prefix