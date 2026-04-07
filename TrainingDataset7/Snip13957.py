def teardown_test_environment():
    """
    Perform any global post-test teardown, such as restoring the original
    template renderer and restoring the email sending functions.
    """
    saved_data = _TestState.saved_data

    settings.ALLOWED_HOSTS = saved_data.allowed_hosts
    settings.DEBUG = saved_data.debug
    settings.EMAIL_BACKEND = saved_data.email_backend
    Template._render = saved_data.template_render
    PartialTemplate._render = saved_data.partial_template_render

    del _TestState.saved_data
    del mail.outbox