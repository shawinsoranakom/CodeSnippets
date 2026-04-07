def mail_managers(
    subject, message, *, fail_silently=False, connection=None, html_message=None
):
    """Send a message to the managers, as defined by the MANAGERS setting."""
    _send_server_message(
        setting_name="MANAGERS",
        subject=subject,
        message=message,
        html_message=html_message,
        fail_silently=fail_silently,
        connection=connection,
    )