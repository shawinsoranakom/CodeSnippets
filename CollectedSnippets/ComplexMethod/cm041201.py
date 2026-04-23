def to_exception(self, error: Error) -> ParameterValidationError:
        error_type, name, additional = error

        if error_type == "missing required field":
            return MissingRequiredField(error)
        elif error_type == "unknown field":
            return UnknownField(error)
        elif error_type == "invalid type":
            return InvalidType(error)
        elif error_type == "invalid range":
            return InvalidRange(error)
        elif error_type == "invalid length":
            return InvalidLength(error)
        elif error_type == "unable to encode to json":
            return JsonEncodingError(error)
        elif error_type == "invalid type for document":
            return InvalidDocumentType(error)
        elif error_type == "more than one input":
            return MoreThanOneInput(error)
        elif error_type == "empty input":
            return EmptyInput(error)

        return ParameterValidationError(error)