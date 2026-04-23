def _plural_string(self):
        """
        Return the plural string (including nplurals) for this catalog
        language, or None if no plural string is available.
        """
        if "" in self.translation._catalog:
            for line in self.translation._catalog[""].split("\n"):
                if line.startswith("Plural-Forms:"):
                    return line.split(":", 1)[1].strip()
        return None