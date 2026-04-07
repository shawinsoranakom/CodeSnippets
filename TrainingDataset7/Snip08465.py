def is_name_available(self, name, max_length=None):
        exceeds_max_length = max_length and len(name) > max_length
        return not self.exists(name) and not exceeds_max_length