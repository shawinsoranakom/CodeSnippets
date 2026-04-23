def mail_admins(
    subject, message, *, fail_silently=False, connection=None, html_message=None
):
    """Send a message to the admins, as defined by the ADMINS setting."""
    _send_server_message(
        setting_name="ADMINS",
        subject=subject,
        message=message,
        html_message=html_message,
        fail_silently=fail_silently,
        connection=connection,
    )