def add_arguments(self, parser):
        parser.add_argument(
            "--%s" % self.UserModel.USERNAME_FIELD,
            help="Specifies the login for the superuser.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help=(
                "Tells Django to NOT prompt the user for input of any kind. "
                "You must use --%s with --noinput, along with an option for "
                "any other required field. Superusers created with --noinput will "
                "not be able to log in until they're given a valid password."
                % self.UserModel.USERNAME_FIELD
            ),
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help='Specifies the database to use. Default is "default".',
        )
        for field_name in self.UserModel.REQUIRED_FIELDS:
            field = self.UserModel._meta.get_field(field_name)
            if field.many_to_many:
                if (
                    field.remote_field.through
                    and not field.remote_field.through._meta.auto_created
                ):
                    raise CommandError(
                        "Required field '%s' specifies a many-to-many "
                        "relation through model, which is not supported." % field_name
                    )
                else:
                    parser.add_argument(
                        "--%s" % field_name,
                        action="append",
                        help=(
                            "Specifies the %s for the superuser. Can be used "
                            "multiple times." % field_name,
                        ),
                    )
            else:
                parser.add_argument(
                    "--%s" % field_name,
                    help="Specifies the %s for the superuser." % field_name,
                )