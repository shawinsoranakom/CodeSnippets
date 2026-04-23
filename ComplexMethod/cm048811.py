def is_valid_structured_reference(reference):
    """Check whether the provided reference is a valid structured reference.
    This is currently supporting SEPA enabled countries. More specifically countries covered by functions in this file.

    :param reference: the reference to check
    """
    reference = sanitize_structured_reference(reference or '')

    return (
        is_valid_structured_reference_be(reference) or
        is_valid_structured_reference_dk(reference) or
        is_valid_structured_reference_fi(reference) or
        is_valid_structured_reference_no_se(reference) or
        is_valid_structured_reference_si(reference) or
        is_valid_structured_reference_nl(reference) or
        is_valid_structured_reference_iso(reference)
    ) if reference else False