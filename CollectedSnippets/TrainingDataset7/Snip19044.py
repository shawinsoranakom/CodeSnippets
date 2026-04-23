def get_unused_country_id(self):
        # Find a serial ID that hasn't been used already and has enough of a
        # buffer for the following `bulk_create` call without an explicit pk
        # not to conflict.
        return getattr(Country.objects.last(), "id", 10) + 100