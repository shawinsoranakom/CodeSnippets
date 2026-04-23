def populate_changes(self, diff: t.Optional[list[str]]) -> None:
        """Populate the changeset using the given diff."""
        patches = parse_diff(diff)
        patches: list[FileDiff] = sorted(patches, key=lambda k: k.new.path)

        self.changes = dict((patch.new.path, tuple(patch.new.ranges)) for patch in patches)

        renames = [patch.old.path for patch in patches if patch.old.path != patch.new.path and patch.old.exists and patch.new.exists]
        deletes = [patch.old.path for patch in patches if not patch.new.exists]

        # make sure old paths which were renamed or deleted are registered in changes
        for path in renames + deletes:
            if path in self.changes:
                # old path was replaced with another file
                continue

            # failed tests involving deleted files should be using line 0 since there is no content remaining
            self.changes[path] = ((0, 0),)