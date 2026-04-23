def intcomma(value, use_l10n=True):
    """
    Convert an integer or float (or a string representation of either) to a
    string containing commas every three digits. Format localization is
    respected. For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    """
    if use_l10n:
        try:
            if not isinstance(value, (float, Decimal)):
                value = Decimal(value)
        except (TypeError, ValueError, InvalidOperation):
            return intcomma(value, False)
        else:
            return number_format(value, use_l10n=True, force_grouping=True)
    result = str(value)
    match = re.match(r"-?\d+", result)
    if match:
        prefix = match[0]
        prefix_with_commas = re.sub(r"\d{3}", r"\g<0>,", prefix[::-1])[::-1]
        # Remove a leading comma, if needed.
        prefix_with_commas = re.sub(r"^(-?),", r"\1", prefix_with_commas)
        result = prefix_with_commas + result[len(prefix) :]
    return result