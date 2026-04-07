def get_matching_imports(self, base_names):
            """
            Return the set of collected imports that start with any
            of the fully-qualified dotted names in iterable base_names.
            """
            matcher = re.compile(
                r"\b(" + r"|".join(re.escape(name) for name in base_names) + r")\b"
            )
            return set(name for name in self.imports if matcher.match(name))