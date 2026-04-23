def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: Callable[[Any], Mapping[str, Any]]
        ) -> Mapping[str, Any]:
            return with_info_plain_validator_function(cls._validate)