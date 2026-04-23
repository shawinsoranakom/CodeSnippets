def get_changelist_filters(self):
        return {
            "is_superuser__exact": 0,
            "is_staff__exact": 0,
        }