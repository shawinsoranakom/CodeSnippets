def get_preserved_filters_querystring(self):
        return urlencode(
            {"_changelist_filters": self.get_changelist_filters_querystring()}
        )