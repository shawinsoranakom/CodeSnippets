def get_connection_params(self):
        kwargs = {
            "conv": django_conversions,
            "charset": "utf8mb4",
        }
        settings_dict = self.settings_dict
        if settings_dict["USER"]:
            kwargs["user"] = settings_dict["USER"]
        if settings_dict["NAME"]:
            kwargs["database"] = settings_dict["NAME"]
        if settings_dict["PASSWORD"]:
            kwargs["password"] = settings_dict["PASSWORD"]
        if settings_dict["HOST"].startswith("/"):
            kwargs["unix_socket"] = settings_dict["HOST"]
        elif settings_dict["HOST"]:
            kwargs["host"] = settings_dict["HOST"]
        if settings_dict["PORT"]:
            kwargs["port"] = int(settings_dict["PORT"])
        # We need the number of potentially affected rows after an
        # "UPDATE", not the number of changed rows.
        kwargs["client_flag"] = CLIENT.FOUND_ROWS
        # Validate the transaction isolation level, if specified.
        options = settings_dict["OPTIONS"].copy()
        isolation_level = options.pop("isolation_level", "read committed")
        if isolation_level:
            isolation_level = isolation_level.lower()
            if isolation_level not in self.isolation_levels:
                raise ImproperlyConfigured(
                    "Invalid transaction isolation level '%s' specified.\n"
                    "Use one of %s, or None."
                    % (
                        isolation_level,
                        ", ".join("'%s'" % s for s in sorted(self.isolation_levels)),
                    )
                )
        self.isolation_level = isolation_level
        kwargs.update(options)
        return kwargs