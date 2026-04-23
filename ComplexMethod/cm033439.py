def validate_parser_dependency(self) -> "CreateDatasetReq":
        """
        Mixed conditional validation:
        - If parser_id is omitted (field not set):
            * If both parse_type and pipeline_id are omitted → default chunk_method = "naive"
            * If both parse_type and pipeline_id are provided → allow ingestion pipeline mode
        - If parser_id is provided (valid enum) → parse_type and pipeline_id must be None (disallow mixed usage)

        Raises:
            PydanticCustomError with code 'dependency_error' on violation.
        """
        # Omitted chunk_method (not in fields) logic
        if self.chunk_method is None and "chunk_method" not in self.model_fields_set:
            # All three absent → default naive
            if self.parse_type is None and self.pipeline_id is None:
                object.__setattr__(self, "chunk_method", "naive")
                return self
            # parser_id omitted: require BOTH parse_type & pipeline_id present (no partial allowed)
            if self.parse_type is None or self.pipeline_id is None:
                missing = []
                if self.parse_type is None:
                    missing.append("parse_type")
                if self.pipeline_id is None:
                    missing.append("pipeline_id")
                raise PydanticCustomError(
                    "dependency_error",
                    "parser_id omitted → required fields missing: {fields}",
                    {"fields": ", ".join(missing)},
                )
            # Both provided → allow pipeline mode
            return self

        # parser_id provided (valid): parse_type MUST be one of [None, 1], and MUST NOT have pipeline_id
        if isinstance(self.chunk_method, str):
            invalid = []
            if self.parse_type not in [None, 1] or self.pipeline_id is not None:
                if self.parse_type not in [None, 1]:
                    invalid.append("parse_type")
                if self.pipeline_id is not None:
                    invalid.append("pipeline_id")
                raise PydanticCustomError(
                    "dependency_error",
                    "parser_id provided → disallowed fields present: {fields}",
                    {"fields": ", ".join(invalid)},
                )
        return self