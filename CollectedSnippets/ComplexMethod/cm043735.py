def validate_form_type(cls, v):
        """Validate form_type."""
        if not v:
            return None
        if isinstance(v, str):
            forms = v.split(",")
        elif isinstance(v, list):
            forms = v
        else:
            raise OpenBBError("Unexpected form_type value.")
        new_forms: list = []
        messages: list = []
        for form in forms:
            if form.upper() in FORM_LIST:
                new_forms.append(form.upper())
            else:
                messages.append(f"Invalid form type: {form}")

        if not new_forms:
            raise OpenBBError(
                f"No valid forms provided -> {', '.join(messages)} -> Valid forms: {', '.join(FORM_LIST)}"
            )

        if new_forms and messages:
            warn("\n ".join(messages))

        return ",".join(new_forms) if len(new_forms) > 1 else new_forms[0]