def _prepare_arguments(self, *args, **kwargs) -> dict[str, Any]:
        """Prepare arguments for SPARC validation."""
        # Remove config parameter if present (not needed for validation)
        clean_kwargs = {k: v for k, v in kwargs.items() if k != "config"}

        # If we have positional args, try to map them to parameter names
        if args and hasattr(self.wrapped_tool, "args_schema"):
            try:
                schema = self.wrapped_tool.args_schema
                field_source = None
                if hasattr(schema, "__fields__"):
                    field_source = schema.__fields__
                elif hasattr(schema, "model_fields"):
                    field_source = schema.model_fields
                if field_source:
                    field_names = list(field_source.keys())
                    for i, arg in enumerate(args):
                        if i < len(field_names):
                            clean_kwargs[field_names[i]] = arg
            except (AttributeError, KeyError, TypeError):
                # If schema parsing fails, just use kwargs
                pass

        return clean_kwargs