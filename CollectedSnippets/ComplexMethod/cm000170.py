def is_valid_email_address(email: str) -> bool:
    """
    Returns True if the passed email address is valid.

    The local part of the email precedes the singular @ symbol and
    is associated with a display-name. For example, "john.smith"
    The domain is stricter than the local part and follows the @ symbol.

    Global email checks:
     1. There can only be one @ symbol in the email address. Technically if the
        @ symbol is quoted in the local-part, then it is valid, however this
        implementation ignores "" for now.
        (See https://en.wikipedia.org/wiki/Email_address#:~:text=If%20quoted,)
     2. The local-part and the domain are limited to a certain number of octets. With
        unicode storing a single character in one byte, each octet is equivalent to
        a character. Hence, we can just check the length of the string.
    Checks for the local-part:
     3. The local-part may contain: upper and lowercase latin letters, digits 0 to 9,
        and printable characters (!#$%&'*+-/=?^_`{|}~)
     4. The local-part may also contain a "." in any place that is not the first or
        last character, and may not have more than one "." consecutively.

    Checks for the domain:
     5. The domain may contain: upper and lowercase latin letters and digits 0 to 9
     6. Hyphen "-", provided that it is not the first or last character
     7. The domain may also contain a "." in any place that is not the first or
        last character, and may not have more than one "." consecutively.

    >>> for email, valid in email_tests:
    ...     assert is_valid_email_address(email) == valid
    """

    # (1.) Make sure that there is only one @ symbol in the email address
    if email.count("@") != 1:
        return False

    local_part, domain = email.split("@")
    # (2.) Check octet length of the local part and domain
    if len(local_part) > MAX_LOCAL_PART_OCTETS or len(domain) > MAX_DOMAIN_OCTETS:
        return False

    # (3.) Validate the characters in the local-part
    if any(
        char not in string.ascii_letters + string.digits + ".(!#$%&'*+-/=?^_`{|}~)"
        for char in local_part
    ):
        return False

    # (4.) Validate the placement of "." characters in the local-part
    if local_part.startswith(".") or local_part.endswith(".") or ".." in local_part:
        return False

    # (5.) Validate the characters in the domain
    if any(char not in string.ascii_letters + string.digits + ".-" for char in domain):
        return False

    # (6.) Validate the placement of "-" characters
    if domain.startswith("-") or domain.endswith("."):
        return False

    # (7.) Validate the placement of "." characters
    return not (domain.startswith(".") or domain.endswith(".") or ".." in domain)