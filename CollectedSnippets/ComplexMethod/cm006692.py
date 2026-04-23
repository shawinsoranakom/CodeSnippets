def _format_markdown_reason(exception: BaseException) -> str:
        """Format the error reason with markdown formatting."""
        reason = f"**{exception.__class__.__name__}**\n"
        if hasattr(exception, "body") and isinstance(exception.body, dict) and "message" in exception.body:
            reason += f" - **{exception.body.get('message')}**\n"
        elif hasattr(exception, "code"):
            reason += f" - **Code: {exception.code}**\n"
        elif hasattr(exception, "args") and exception.args:
            reason += f" - **Details: {exception.args[0]}**\n"
        elif isinstance(exception, ValidationError):
            reason += f" - **Details:**\n\n```python\n{exception!s}\n```\n"
        else:
            reason += " - **An unknown error occurred.**\n"
        return reason