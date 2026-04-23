def get_connection_params(self):
        settings_dict = self.settings_dict
        if not settings_dict["NAME"]:
            raise ImproperlyConfigured(
                "settings.DATABASES is improperly configured. "
                "Please supply the NAME value."
            )
        kwargs = {
            "database": settings_dict["NAME"],
            "detect_types": Database.PARSE_DECLTYPES | Database.PARSE_COLNAMES,
            **settings_dict["OPTIONS"],
        }
        # Always allow the underlying SQLite connection to be shareable
        # between multiple threads. The safe-guarding will be handled at a
        # higher level by the `BaseDatabaseWrapper.allow_thread_sharing`
        # property. This is necessary as the shareability is disabled by
        # default in sqlite3 and it cannot be changed once a connection is
        # opened.
        if "check_same_thread" in kwargs and kwargs["check_same_thread"]:
            warnings.warn(
                "The `check_same_thread` option was provided and set to "
                "True. It will be overridden with False. Use the "
                "`DatabaseWrapper.allow_thread_sharing` property instead "
                "for controlling thread shareability.",
                RuntimeWarning,
            )
        kwargs.update({"check_same_thread": False, "uri": True})
        transaction_mode = kwargs.pop("transaction_mode", None)
        if (
            transaction_mode is not None
            and transaction_mode.upper() not in self.transaction_modes
        ):
            allowed_transaction_modes = ", ".join(
                [f"{mode!r}" for mode in sorted(self.transaction_modes)]
            )
            raise ImproperlyConfigured(
                f"settings.DATABASES[{self.alias!r}]['OPTIONS']['transaction_mode'] "
                f"is improperly configured to '{transaction_mode}'. Use one of "
                f"{allowed_transaction_modes}, or None."
            )
        self.transaction_mode = transaction_mode.upper() if transaction_mode else None

        init_command = kwargs.pop("init_command", "")
        self.init_commands = init_command.split(";")
        return kwargs