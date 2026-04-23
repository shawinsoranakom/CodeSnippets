def all_replaced_applied(self, migration_key, applied):
        """
        Checks (recursively) whether all replaced migrations are applied.
        """
        if migration_key in self.replacements:
            for replaced_key in self.replacements[migration_key].replaces:
                if replaced_key not in applied and not self.all_replaced_applied(
                    replaced_key, applied
                ):
                    return False
            return True

        return False