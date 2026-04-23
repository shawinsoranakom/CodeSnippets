def _get_exception_message(self, e: Exception):
        """Get a message from an OpenAI exception.

        Args:
            e (Exception): The exception to get the message from.

        Returns:
            str: The message from the exception.
        """
        try:
            from openai import BadRequestError, NotFoundError
        except ImportError:
            return None
        if isinstance(e, NotFoundError):
            body = getattr(e, "body", None) or {}
            if isinstance(body, dict) and body.get("code") == "model_not_found":
                return (
                    f"Model '{self.model_name}' is not available for this OpenAI account. "
                    "Your API tier may not have access yet — check "
                    "https://platform.openai.com/settings/organization/limits "
                    "or select a different model."
                )
        if isinstance(e, BadRequestError):
            message = e.body.get("message")
            if message:
                return message
        return None