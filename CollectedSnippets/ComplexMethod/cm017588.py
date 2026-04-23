def _check_actions(self, obj):
        errors = []
        actions = obj._get_base_actions()

        # Actions with an allowed_permission attribute require the ModelAdmin
        # to implement a has_<perm>_permission() method for each permission.
        for func, name, _ in actions:
            if not hasattr(func, "allowed_permissions"):
                continue
            for permission in func.allowed_permissions:
                method_name = "has_%s_permission" % permission
                if not hasattr(obj, method_name):
                    errors.append(
                        checks.Error(
                            "%s must define a %s() method for the %s action."
                            % (
                                obj.__class__.__name__,
                                method_name,
                                func.__name__,
                            ),
                            obj=obj.__class__,
                            id="admin.E129",
                        )
                    )
        # Names need to be unique.
        names = collections.Counter(name for _, name, _ in actions)
        for name, count in names.items():
            if count > 1:
                errors.append(
                    checks.Error(
                        "__name__ attributes of actions defined in %s must be "
                        "unique. Name %r is not unique."
                        % (
                            obj.__class__.__name__,
                            name,
                        ),
                        obj=obj.__class__,
                        id="admin.E130",
                    )
                )
        return errors