def _clean_credentials(credentials):
    """
    Clean a dictionary of credentials of potentially sensitive info before
    sending to less secure functions.

    Not comprehensive - intended for user_login_failed signal
    """
    SENSITIVE_CREDENTIALS = re.compile("api|token|key|secret|password|signature", re.I)
    CLEANSED_SUBSTITUTE = "********************"
    for key in credentials:
        if SENSITIVE_CREDENTIALS.search(key):
            credentials[key] = CLEANSED_SUBSTITUTE
    return credentials