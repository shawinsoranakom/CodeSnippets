def get_error_message(self):
        return (
            ngettext(
                "This password is too short. It must contain at least %d character.",
                "This password is too short. It must contain at least %d characters.",
                self.min_length,
            )
            % self.min_length
        )