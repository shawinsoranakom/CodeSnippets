def mail_prepare_for_domain_search(email, min_email_length=0):
    """ Return an email address to use for a domain-based search. For generic
    email providers like gmail (see ``_MAIL_DOMAIN_BLACKLIST``) we consider
    each email as being independant (and return the whole email). Otherwise
    we return only the right-part of the email (aka "mydomain.com" if email is
    "Raoul Lachignole" <raoul@mydomain.com>).

    :param integer min_email_length: skip if email has not the sufficient minimal
      length, indicating a probably fake / wrong value (skip if 0);
    """
    if not email:
        return False
    email_tocheck = email_normalize(email, strict=False)
    if not email_tocheck:
        email_tocheck = email.casefold()

    if email_tocheck and min_email_length and len(email_tocheck) < min_email_length:
        return False

    parts = email_tocheck.rsplit('@', maxsplit=1)
    if len(parts) == 1:
        return email_tocheck
    email_domain = parts[1]
    if email_domain not in _MAIL_DOMAIN_BLACKLIST:
        return '@' + email_domain
    return email_tocheck