def __getitem__(self, perm_name):
        return self.user.has_perm("%s.%s" % (self.app_label, perm_name))