def get_json_data(self, escape_html=False):
        errors = []
        for error in self.as_data():
            message = next(iter(error))
            errors.append(
                {
                    "message": escape(message) if escape_html else message,
                    "code": error.code or "",
                }
            )
        return errors