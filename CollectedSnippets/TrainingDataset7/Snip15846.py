def test_invalid_choice_db_option(self):
        if PY314:
            expected_error = (
                r"Error: argument --database: invalid choice: 'deflaut', "
                r"maybe you meant 'default'\? \(choose from default, other\)"
            )
        else:
            expected_error = (
                r"Error: argument --database: invalid choice: 'deflaut' "
                r"\(choose from '?default'?, '?other'?\)"
            )
        args = [
            "changepassword",
            "createsuperuser",
            "remove_stale_contenttypes",
            "check",
            "createcachetable",
            "dbshell",
            "flush",
            "dumpdata",
            "inspectdb",
            "loaddata",
            "showmigrations",
            "sqlflush",
            "sqlmigrate",
            "sqlsequencereset",
            "migrate",
        ]

        for arg in args:
            with self.assertRaisesRegex(CommandError, expected_error):
                call_command(arg, "--database", "deflaut", verbosity=0)