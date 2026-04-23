def find_fixtures(self, fixture_label):
        """Find fixture files for a given label."""
        if fixture_label == READ_STDIN:
            return [(READ_STDIN, None, READ_STDIN)]

        fixture_name, ser_fmt, cmp_fmt = self.parse_name(fixture_label)
        if self.verbosity >= 2:
            self.stdout.write("Loading '%s' fixtures..." % fixture_name)

        fixture_name, fixture_dirs = self.get_fixture_name_and_dirs(fixture_name)
        targets = self.get_targets(fixture_name, ser_fmt, cmp_fmt)
        fixture_files = []
        for fixture_dir in fixture_dirs:
            if self.verbosity >= 2:
                self.stdout.write("Checking %s for fixtures..." % humanize(fixture_dir))
            fixture_files_in_dir = self.find_fixture_files_in_dir(
                fixture_dir,
                fixture_name,
                targets,
            )
            if self.verbosity >= 2 and not fixture_files_in_dir:
                self.stdout.write(
                    "No fixture '%s' in %s." % (fixture_name, humanize(fixture_dir))
                )

            # Check kept for backwards-compatibility; it isn't clear why
            # duplicates are only allowed in different directories.
            if len(fixture_files_in_dir) > 1:
                raise CommandError(
                    "Multiple fixtures named '%s' in %s. Aborting."
                    % (fixture_name, humanize(fixture_dir))
                )
            fixture_files.extend(fixture_files_in_dir)

        if not fixture_files:
            raise CommandError("No fixture named '%s' found." % fixture_name)

        return fixture_files