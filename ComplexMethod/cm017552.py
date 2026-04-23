def check(self, **kwargs):
        errors = []
        if not isinstance(settings.STATICFILES_DIRS, (list, tuple)):
            errors.append(
                Error(
                    "The STATICFILES_DIRS setting is not a tuple or list.",
                    hint="Perhaps you forgot a trailing comma?",
                    id="staticfiles.E001",
                )
            )
            return errors
        for root in settings.STATICFILES_DIRS:
            if isinstance(root, (list, tuple)):
                prefix, root = root
                if prefix.endswith("/"):
                    errors.append(
                        Error(
                            "The prefix %r in the STATICFILES_DIRS setting must "
                            "not end with a slash." % prefix,
                            id="staticfiles.E003",
                        )
                    )
            if settings.STATIC_ROOT and os.path.abspath(
                settings.STATIC_ROOT
            ) == os.path.abspath(root):
                errors.append(
                    Error(
                        "The STATICFILES_DIRS setting should not contain the "
                        "STATIC_ROOT setting.",
                        id="staticfiles.E002",
                    )
                )
            if not os.path.isdir(root):
                errors.append(
                    Warning(
                        f"The directory '{root}' in the STATICFILES_DIRS setting "
                        f"does not exist.",
                        id="staticfiles.W004",
                    )
                )
        return errors