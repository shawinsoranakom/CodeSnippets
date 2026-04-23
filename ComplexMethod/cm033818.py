def applies_to(self, path, name=None):  # type: (str, t.Optional[str]) -> bool
        """Return True if this entry applies to the given path, otherwise return False."""
        if self.names:
            if not name:
                return False

            if name not in self.names:
                return False

        if self.ignore_paths and any(path.endswith(ignore_path) for ignore_path in self.ignore_paths):
            return False

        if self.ansible_test_only and '/test/lib/ansible_test/_internal/' not in path:
            return False

        if self.modules_only:
            return is_module_path(path)

        return True