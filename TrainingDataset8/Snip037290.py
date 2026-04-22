def set_value(self, value: Any, where_defined: Optional[str] = None) -> None:
        """Set the value of this option.

        Parameters
        ----------
        value
            The new value for this parameter.
        where_defined : str
            New value to remember where this parameter was set.

        """
        self._get_val_func = lambda: value

        if where_defined is None:
            self.where_defined = ConfigOption.DEFAULT_DEFINITION
        else:
            self.where_defined = where_defined

        self.is_default = value == self.default_val

        if self.deprecated and self.where_defined != ConfigOption.DEFAULT_DEFINITION:

            details = {
                "key": self.key,
                "file": self.where_defined,
                "explanation": self.deprecation_text,
                "date": self.expiration_date,
            }

            if self.is_expired():
                raise DeprecationError(
                    textwrap.dedent(
                        """
                    ════════════════════════════════════════════════
                    %(key)s IS NO LONGER SUPPORTED.

                    %(explanation)s

                    Please update %(file)s.
                    ════════════════════════════════════════════════
                    """
                    )
                    % details
                )
            else:
                # Import here to avoid circular imports
                from streamlit.logger import get_logger

                LOGGER = get_logger(__name__)
                LOGGER.warning(
                    textwrap.dedent(
                        """
                    ════════════════════════════════════════════════
                    %(key)s IS DEPRECATED.
                    %(explanation)s

                    This option will be removed on or after %(date)s.

                    Please update %(file)s.
                    ════════════════════════════════════════════════
                    """
                    )
                    % details
                )