def find(self, path, find_all=False):
        """
        Look for files in the extra locations as defined in STATICFILES_DIRS.
        """
        matches = []
        for prefix, root in self.locations:
            if root not in searched_locations:
                searched_locations.append(root)
            matched_path = self.find_location(root, path, prefix)
            if matched_path:
                if not find_all:
                    return matched_path
                matches.append(matched_path)
        return matches