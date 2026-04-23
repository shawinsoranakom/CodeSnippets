def timezone_name(self):
        """
        Name of the time zone of the database connection.
        """
        if not settings.USE_TZ:
            return settings.TIME_ZONE
        elif self.settings_dict["TIME_ZONE"] is None:
            return "UTC"
        else:
            return self.settings_dict["TIME_ZONE"]