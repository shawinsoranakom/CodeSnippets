def _load_chat_template(
    chat_template: Path | str | None,
    *,
    is_literal: bool = False,
) -> str | None:
    if chat_template is None:
        return None

    if is_literal:
        if isinstance(chat_template, Path):
            raise TypeError(
                "chat_template is expected to be read directly from its value"
            )

        return chat_template

    try:
        with open(chat_template) as f:
            return f.read()
    except OSError as e:
        if isinstance(chat_template, Path):
            raise

        JINJA_CHARS = "{}\n"
        if not any(c in chat_template for c in JINJA_CHARS):
            # Try to load from the built-in templates directory
            from vllm.transformers_utils.chat_templates.registry import (
                CHAT_TEMPLATES_DIR,
            )

            builtin_template_path = CHAT_TEMPLATES_DIR / chat_template
            try:
                with open(builtin_template_path) as f:
                    return f.read()
            except OSError:
                msg = (
                    f"The supplied chat template ({chat_template}) "
                    f"looks like a file path, but it failed to be opened. "
                    f"Tried: {chat_template} and {builtin_template_path}. "
                    f"Reason: {e}"
                )
                raise ValueError(msg) from e

        # If opening a file fails, set chat template to be args to
        # ensure we decode so our escape are interpreted correctly
        return _load_chat_template(chat_template, is_literal=True)