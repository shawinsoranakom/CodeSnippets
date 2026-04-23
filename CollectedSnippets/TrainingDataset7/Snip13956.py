def setup_test_environment(debug=None):
    """
    Perform global pre-test setup, such as installing the instrumented template
    renderer and setting the email backend to the locmem email backend.
    """
    if hasattr(_TestState, "saved_data"):
        # Executing this function twice would overwrite the saved values.
        raise RuntimeError(
            "setup_test_environment() was already called and can't be called "
            "again without first calling teardown_test_environment()."
        )

    if debug is None:
        debug = settings.DEBUG

    saved_data = SimpleNamespace()
    _TestState.saved_data = saved_data

    saved_data.allowed_hosts = settings.ALLOWED_HOSTS
    # Add the default host of the test client.
    settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "testserver"]

    saved_data.debug = settings.DEBUG
    settings.DEBUG = debug

    saved_data.email_backend = settings.EMAIL_BACKEND
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    saved_data.template_render = Template._render
    saved_data.partial_template_render = PartialTemplate._render
    Template._render = instrumented_test_render
    PartialTemplate._render = instrumented_test_render

    mail.outbox = []

    deactivate()