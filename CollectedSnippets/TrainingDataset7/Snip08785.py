def find_fixture_files_in_dir(self, fixture_dir, fixture_name, targets):
        fixture_files_in_dir = []
        path = os.path.join(fixture_dir, fixture_name)
        for candidate in glob.iglob(glob.escape(path) + "*"):
            if os.path.basename(candidate) in targets:
                # Save the fixture_dir and fixture_name for future error
                # messages.
                fixture_files_in_dir.append((candidate, fixture_dir, fixture_name))
        return fixture_files_in_dir