def databases(self):
        # Maintained for backward compatibility as some 3rd party packages have
        # made use of this private API in the past. It is no longer used within
        # Django itself.
        return self.settings