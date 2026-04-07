def is_in_memory_db(self):
        return self.creation.is_in_memory_db(self.settings_dict["NAME"])