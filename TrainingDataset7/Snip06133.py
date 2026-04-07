def __getitem__(self, app_label):
        return PermLookupDict(self.user, app_label)