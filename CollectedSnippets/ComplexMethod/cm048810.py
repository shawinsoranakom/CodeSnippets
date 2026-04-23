def is_valid_structured_reference_si(reference):
    """ Validates a Slovenian structured reference using Model 01 (SI01).

        Format: SI01 (P1-P2-P3)K
        - Starts with 'SI01'
        - P1, P2, P3 are numeric segments (max 20 digits total, up to 2 hyphens)
        - K is a check digit calculated using MOD 11

        :param reference: the reference to check
        :return: True if reference is a structured reference, False otherwise
    """
    sanitized_reference = sanitize_structured_reference(reference)

    if sanitized_reference.startswith('SI01'):
        sanitized_reference = sanitized_reference[4:]  # Remove SI01
    else:
        return False

    # Contains maximum of two hyphens
    if sanitized_reference.count('-') > 2:
        return False

    # Validate hyphenated parts using regex: 3 numeric parts (last ends with check digit)
    match = re.match(r'^(\d+)-(\d+)-(\d+)$', sanitized_reference)
    if not match:
        return False

    # Split into main digits and check digit
    core = sanitized_reference.replace('-', '')
    if not core.isdigit() or len(core) < 2:
        return False

    digits, given_check_digit = core[:-1], core[-1]

    weights = list(range(2, 14))
    weights = weights[0:len(digits)]
    weighted_sum = sum(int(d) * w for d, w in zip(reversed(digits), weights))

    expected_check_digit = 11 - (weighted_sum % 11)
    if expected_check_digit in (10, 11):
        expected_check_digit = 0

    return given_check_digit == str(expected_check_digit)