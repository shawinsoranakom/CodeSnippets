def validate_name(self, name, name_or_dir="name"):
        if name is None:
            raise CommandError(
                "you must provide {an} {app} name".format(
                    an=self.a_or_an,
                    app=self.app_or_project,
                )
            )
        # Check it's a valid directory name.
        if not name.isidentifier():
            raise CommandError(
                "'{name}' is not a valid {app} {type}. Please make sure the "
                "{type} is a valid identifier.".format(
                    name=name,
                    app=self.app_or_project,
                    type=name_or_dir,
                )
            )
        # Check that __spec__ doesn't exist.
        if find_spec(name) is not None:
            raise CommandError(
                "'{name}' conflicts with the name of an existing Python "
                "module and cannot be used as {an} {app} {type}. Please try "
                "another {type}.".format(
                    name=name,
                    an=self.a_or_an,
                    app=self.app_or_project,
                    type=name_or_dir,
                )
            )