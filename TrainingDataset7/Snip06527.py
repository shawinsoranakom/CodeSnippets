def ready(self):
        serializers.BUILTIN_SERIALIZERS.setdefault(
            "geojson", "django.contrib.gis.serializers.geojson"
        )