def _verify_email(email: str) -> _Activation:
    """Verify the user's email address.

    The email can either be an empty string (if the user chooses not to enter
    it), or a string with a single '@' somewhere in it.

    Parameters
    ----------
    email : str

    Returns
    -------
    _Activation
        An _Activation object. Its 'is_valid' property will be True only if
        the email was validated.

    """
    email = email.strip()

    # We deliberately use simple email validation here
    # since we do not use email address anywhere to send emails.
    if len(email) > 0 and email.count("@") != 1:
        LOGGER.error("That doesn't look like an email :(")
        return _Activation(None, False)

    return _Activation(email, True)