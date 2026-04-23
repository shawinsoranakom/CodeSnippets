def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: Callable[[Any], Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        from ._compat.v2 import with_info_plain_validator_function

        return with_info_plain_validator_function(cls._validate)