def compiler_deprecated_warning(
        self,
        func: Function,
        parameters: list[Parameter],
    ) -> str | None:
        minversion: VersionTuple | None = None
        for p in parameters:
            for version in p.deprecated_positional, p.deprecated_keyword:
                if version and (not minversion or minversion > version):
                    minversion = version
        if not minversion:
            return None

        # Format the preprocessor warning and error messages.
        assert isinstance(self.cpp.filename, str)
        message = f"Update the clinic input of {func.full_name!r}."
        code = self.COMPILER_DEPRECATION_WARNING_PROTOTYPE.format(
            major=minversion[0],
            minor=minversion[1],
            message=libclinic.c_str_repr(message),
        )
        return libclinic.normalize_snippet(code)