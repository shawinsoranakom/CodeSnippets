def send_mass_mail(
    datatuple,
    *,
    fail_silently=False,
    auth_user=None,
    auth_password=None,
    connection=None,
):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), send
    each message to each recipient list. Return the number of emails sent.

    If from_email is None, use the DEFAULT_FROM_EMAIL setting.
    If auth_user and auth_password are set, use them to log in.
    If auth_user is None, use the EMAIL_HOST_USER setting.
    If auth_password is None, use the EMAIL_HOST_PASSWORD setting.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    if connection is not None:
        if fail_silently:
            raise TypeError(
                "fail_silently cannot be used with a connection. "
                "Pass fail_silently to get_connection() instead."
            )
        if auth_user is not None or auth_password is not None:
            raise TypeError(
                "auth_user and auth_password cannot be used with a connection. "
                "Pass auth_user and auth_password to get_connection() instead."
            )
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )
    messages = [
        EmailMessage(subject, message, sender, recipient, connection=connection)
        for subject, message, sender, recipient in datatuple
    ]
    return connection.send_messages(messages)