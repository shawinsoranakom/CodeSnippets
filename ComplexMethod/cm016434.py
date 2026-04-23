def GET_SCHEMA(cls) -> Schema:
        """Validate node class, finalize schema, validate schema, and set expected class properties."""
        cls.VALIDATE_CLASS()
        schema = cls.FINALIZE_SCHEMA()
        schema.validate()
        if cls._DESCRIPTION is None:
            cls._DESCRIPTION = schema.description
        if cls._CATEGORY is None:
            cls._CATEGORY = schema.category
        if cls._EXPERIMENTAL is None:
            cls._EXPERIMENTAL = schema.is_experimental
        if cls._DEPRECATED is None:
            cls._DEPRECATED = schema.is_deprecated
        if cls._DEV_ONLY is None:
            cls._DEV_ONLY = schema.is_dev_only
        if cls._API_NODE is None:
            cls._API_NODE = schema.is_api_node
        if cls._OUTPUT_NODE is None:
            cls._OUTPUT_NODE = schema.is_output_node
        if cls._HAS_INTERMEDIATE_OUTPUT is None:
            cls._HAS_INTERMEDIATE_OUTPUT = schema.has_intermediate_output
        if cls._INPUT_IS_LIST is None:
            cls._INPUT_IS_LIST = schema.is_input_list
        if cls._NOT_IDEMPOTENT is None:
            cls._NOT_IDEMPOTENT = schema.not_idempotent
        if cls._ACCEPT_ALL_INPUTS is None:
            cls._ACCEPT_ALL_INPUTS = schema.accept_all_inputs

        if cls._RETURN_TYPES is None:
            output = []
            output_name = []
            output_is_list = []
            output_tooltips = []
            if schema.outputs:
                for o in schema.outputs:
                    output.append(o.io_type)
                    output_name.append(o.display_name if o.display_name else o.io_type)
                    output_is_list.append(o.is_output_list)
                    output_tooltips.append(o.tooltip if o.tooltip else None)

            cls._RETURN_TYPES = output
            cls._RETURN_NAMES = output_name
            cls._OUTPUT_IS_LIST = output_is_list
            cls._OUTPUT_TOOLTIPS = output_tooltips
        cls.SCHEMA = schema
        return schema