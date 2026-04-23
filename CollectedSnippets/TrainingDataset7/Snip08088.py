def _simple_domain_name_validator(value):
    """
    Validate that the given value contains no whitespaces to prevent common
    typos.
    """
    checks = ((s in value) for s in string.whitespace)
    if any(checks):
        raise ValidationError(
            _("The domain name cannot contain any spaces or tabs."),
            code="invalid",
        )