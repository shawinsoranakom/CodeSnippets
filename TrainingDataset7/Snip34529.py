def setup(templates, *args, test_once=False, debug_only=False):
    """
    Runs test method multiple times in the following order:

    debug       cached      string_if_invalid
    -----       ------      -----------------
    False       False
    False       True
    False       False       INVALID
    False       True        INVALID
    True        False
    True        True

    Use test_once=True to test deprecation warnings since the message won't be
    displayed multiple times.
    """

    for arg in args:
        templates.update(arg)

    # numerous tests make use of an inclusion tag
    # add this in here for simplicity
    templates["inclusion.html"] = "{{ result }}"

    loaders = [
        (
            "django.template.loaders.cached.Loader",
            [
                ("django.template.loaders.locmem.Loader", templates),
            ],
        ),
    ]

    def decorator(func):
        # Make Engine.get_default() raise an exception to ensure that tests
        # are properly isolated from Django's global settings.
        @override_settings(TEMPLATES=None)
        @wraps(func)
        def inner(self):
            # Set up custom template tag libraries if specified
            libraries = getattr(self, "libraries", {})

            self.engine = Engine(
                libraries=libraries,
                loaders=loaders,
                debug=debug_only,
            )
            func(self)
            if test_once:
                return
            func(self)
            if debug_only:
                return

            self.engine = Engine(
                libraries=libraries,
                loaders=loaders,
                string_if_invalid="INVALID",
            )
            func(self)
            func(self)

            self.engine = Engine(
                debug=True,
                libraries=libraries,
                loaders=loaders,
            )
            func(self)
            func(self)

        return inner

    return decorator