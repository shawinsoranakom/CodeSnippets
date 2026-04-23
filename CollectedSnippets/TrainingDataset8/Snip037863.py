def activate(self, show_instructions: bool = True) -> None:
        """Activate Streamlit.

        Used by `streamlit activate`.
        """
        try:
            self.load()
        except RuntimeError:
            # Runtime Error is raised if credentials file is not found. In that case,
            # `self.activation` is None and we will show the activation prompt below.
            pass

        if self.activation:
            if self.activation.is_valid:
                _exit("Already activated")
            else:
                _exit(
                    "Activation not valid. Please run "
                    "`streamlit activate reset` then `streamlit activate`"
                )
        else:
            activated = False

            while not activated:
                email = click.prompt(
                    text=_EMAIL_PROMPT, prompt_suffix="", default="", show_default=False
                )

                self.activation = _verify_email(email)
                if self.activation.is_valid:
                    self.save()
                    click.secho(_TELEMETRY_TEXT)
                    if show_instructions:
                        click.secho(_INSTRUCTIONS_TEXT)
                    activated = True
                else:  # pragma: nocover
                    LOGGER.error("Please try again.")