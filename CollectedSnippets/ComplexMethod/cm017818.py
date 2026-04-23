def run_checks(
        self,
        app_configs=None,
        tags=None,
        include_deployment_checks=False,
        databases=None,
    ):
        """
        Run all registered checks and return list of Errors and Warnings.
        """
        errors = []
        checks = self.get_checks(include_deployment_checks)

        if tags is not None:
            checks = [check for check in checks if not set(check.tags).isdisjoint(tags)]
        elif not databases:
            # By default, 'database'-tagged checks are not run if an alias
            # is not explicitly specified as they do more than mere static
            # code analysis.
            checks = [check for check in checks if Tags.database not in check.tags]

        if databases is None:
            databases = list(connections)

        for check in checks:
            new_errors = check(app_configs=app_configs, databases=databases)
            if not isinstance(new_errors, Iterable):
                raise TypeError(
                    "The function %r did not return a list. All functions "
                    "registered with the checks registry must return a list." % check,
                )
            errors.extend(new_errors)
        return errors