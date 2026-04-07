def _get_inactive_language_code(self):
        """Return language code for a language which is not activated."""
        current_language = get_language()
        return [code for code, name in settings.LANGUAGES if code != current_language][
            0
        ]