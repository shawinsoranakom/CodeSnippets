def _check_swappable(cls):
        """Check if the swapped model exists."""
        errors = []
        if cls._meta.swapped:
            try:
                apps.get_model(cls._meta.swapped)
            except ValueError:
                errors.append(
                    checks.Error(
                        "'%s' is not of the form 'app_label.app_name'."
                        % cls._meta.swappable,
                        id="models.E001",
                    )
                )
            except LookupError:
                app_label, model_name = cls._meta.swapped.split(".")
                errors.append(
                    checks.Error(
                        "'%s' references '%s.%s', which has not been "
                        "installed, or is abstract."
                        % (cls._meta.swappable, app_label, model_name),
                        id="models.E002",
                    )
                )
        return errors