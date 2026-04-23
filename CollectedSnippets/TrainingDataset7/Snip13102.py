def exception_class(self):
        # Lazy resolve the exception class.
        exception_class = import_string(self.exception_class_path)

        if not isclass(exception_class) or not issubclass(
            exception_class, BaseException
        ):
            raise ValueError(
                f"{self.exception_class_path!r} does not reference a valid exception."
            )
        return exception_class