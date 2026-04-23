def handle(self, **options):
        connection = connections[options["database"]]
        try:
            connection.client.runshell(options["parameters"])
        except FileNotFoundError:
            # Note that we're assuming the FileNotFoundError relates to the
            # command missing. It could be raised for some other reason, in
            # which case this error message would be inaccurate. Still, this
            # message catches the common case.
            raise CommandError(
                "You appear not to have the %r program installed or on your path."
                % connection.client.executable_name
            )
        except subprocess.CalledProcessError as e:
            raise CommandError(
                '"%s" returned non-zero exit status %s.'
                % (
                    " ".join(map(str, e.cmd)),
                    e.returncode,
                ),
                returncode=e.returncode,
            )