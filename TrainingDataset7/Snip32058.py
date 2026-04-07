def receiver(self, **kwargs):
        """
        A receiver that fails while certain settings are being changed.
        - SETTING_BOTH raises an error while receiving the signal
          on both entering and exiting the context manager.
        - SETTING_ENTER raises an error only on enter.
        - SETTING_EXIT raises an error only on exit.
        """
        setting = kwargs["setting"]
        enter = kwargs["enter"]
        if setting in ("SETTING_BOTH", "SETTING_ENTER") and enter:
            raise SettingChangeEnterException
        if setting in ("SETTING_BOTH", "SETTING_EXIT") and not enter:
            raise SettingChangeExitException