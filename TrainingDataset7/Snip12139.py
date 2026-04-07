def quote_name_unless_alias(self, name):
        warnings.warn(
            (
                "SQLCompiler.quote_name_unless_alias() is deprecated. "
                "Use .quote_name() instead."
            ),
            category=RemovedInDjango70Warning,
            skip_file_prefixes=django_file_prefixes(),
        )
        return self.quote_name(name)