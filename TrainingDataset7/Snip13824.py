def clear_serializers_cache(*, setting, **kwargs):
    if setting == "SERIALIZATION_MODULES":
        from django.core import serializers

        serializers._serializers = {}