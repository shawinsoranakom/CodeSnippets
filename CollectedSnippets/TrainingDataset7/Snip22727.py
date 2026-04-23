def jinja2_tests(test_func):
    test_func = skipIf(jinja2 is None, "this test requires jinja2")(test_func)
    return override_settings(
        FORM_RENDERER="django.forms.renderers.Jinja2",
        TEMPLATES={"BACKEND": "django.template.backends.jinja2.Jinja2"},
    )(test_func)