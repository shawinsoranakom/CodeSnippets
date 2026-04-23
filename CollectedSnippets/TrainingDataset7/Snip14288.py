def __getitem__(self, key):
        return self.parent_dict[self.deferred_key][key]