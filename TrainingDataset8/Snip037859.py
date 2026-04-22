def load(self, auto_resolve=False) -> None:
        """Load from toml file."""
        if self.activation is not None:
            LOGGER.error("Credentials already loaded. Not rereading file.")
            return

        try:
            with open(self._conf_file, "r") as f:
                data = toml.load(f).get("general")
            if data is None:
                raise Exception
            self.activation = _verify_email(data.get("email"))
        except FileNotFoundError:
            if auto_resolve:
                self.activate(show_instructions=not auto_resolve)
                return
            raise RuntimeError(
                'Credentials not found. Please run "streamlit activate".'
            )
        except Exception:
            if auto_resolve:
                self.reset()
                self.activate(show_instructions=not auto_resolve)
                return
            raise Exception(
                textwrap.dedent(
                    """
                Unable to load credentials from %s.
                Run "streamlit reset" and try again.
                """
                )
                % (self._conf_file)
            )