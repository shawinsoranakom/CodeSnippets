def get_changelist_filters_querystring(self):
        return urlencode(self.get_changelist_filters())