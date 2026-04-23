def _generate_temp_name(self, for_name):
        """Generate temporary names for workarounds that need temp columns."""
        suffix = hex(hash(for_name)).upper()[1:]
        return self.normalize_name(for_name + "_" + suffix)