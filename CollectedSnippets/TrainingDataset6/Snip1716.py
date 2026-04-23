def __get_pydantic_json_schema__(
            cls, core_schema: Mapping[str, Any], handler: GetJsonSchemaHandler
        ) -> dict[str, Any]:
            return {"type": "string", "format": "email"}