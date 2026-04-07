def location(self, obj):
        return reverse(
            "django.contrib.gis.sitemaps.views.%s" % self.geo_format,
            kwargs={
                "label": obj[0],
                "model": obj[1],
                "field_name": obj[2],
            },
        )