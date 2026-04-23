def from_input(
        advanced_security_options: AdvancedSecurityOptionsInput | None,
    ) -> "SecurityOptions":
        """
        Parses the given AdvancedSecurityOptionsInput, performs some validation, and returns the parsed SecurityOptions.
        If unsupported settings are used, the SecurityOptions are disabled and a warning is logged.

        :param advanced_security_options: of the domain which will be created
        :return: parsed SecurityOptions
        :raises: ValidationException in case the given AdvancedSecurityOptions are invalid
        """
        if advanced_security_options is None:
            return SecurityOptions(enabled=False, master_username=None, master_password=None)
        if not advanced_security_options.get("InternalUserDatabaseEnabled", False):
            LOG.warning(
                "AdvancedSecurityOptions are set, but InternalUserDatabase is disabled. Disabling security options."
            )
            return SecurityOptions(enabled=False, master_username=None, master_password=None)

        master_username = advanced_security_options.get("MasterUserOptions", {}).get(
            "MasterUserName", None
        )
        master_password = advanced_security_options.get("MasterUserOptions", {}).get(
            "MasterUserPassword", None
        )
        if not master_username and not master_password:
            raise ValidationException(
                "You must provide a master username and password when the internal user database is enabled."
            )
        if not master_username or not master_password:
            raise ValidationException("You must provide a master username and password together.")

        return SecurityOptions(
            enabled=advanced_security_options["Enabled"] or False,
            master_username=master_username,
            master_password=master_password,
        )