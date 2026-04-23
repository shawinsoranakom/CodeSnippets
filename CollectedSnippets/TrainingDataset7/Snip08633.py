def send_mail(
    subject,
    message,
    from_email,
    recipient_list,
    *,
    fail_silently=False,
    auth_user=None,
    auth_password=None,
    connection=None,
    html_message=None,
):
    """
    Easy wrapper for sending a single message to a recipient list. All members
    of the recipient list will see the other recipients in the 'To' field.

    If from_email is None, use the DEFAULT_FROM_EMAIL setting.
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
    mail = EmailMultiAlternatives(
        subject, message, from_email, recipient_list, connection=connection
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")

    return mail.send()