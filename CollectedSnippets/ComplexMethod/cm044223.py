def _extract_info(
        fetcher: Fetcher, type_: Literal["query_params", "data"]
    ) -> tuple:
        """Extract info (fields and docstring) from fetcher query params or data."""
        model: BaseModel = RegistryMap._get_model(fetcher, type_)
        standard_info: dict[str, Any] = {"fields": {}, "docstring": None}
        extra_info: dict[str, Any] = {"fields": {}, "docstring": model.__doc__}
        found_first_standard = False

        family = RegistryMap._get_class_family(model)
        for i, child in enumerate(family):
            if child.__name__ in SKIP:
                continue

            parent = family[i + 1] if family[i + 1] not in SKIP else BaseModel

            fields = {
                name: field
                for name, field in child.model_fields.items()
                # This ensures fields inherited by c are discarded.
                # We need to compare child and parent __annotations__
                # because this attribute is redirected to the parent class
                # when the child simply inherits the parent and does not
                # define any attributes.
                # TLDR: Only fields defined in c are included
                if name in child.__annotations__
                and child.__annotations__ is not parent.__annotations__
            }

            if Path(getfile(child)).parent == STANDARD_MODELS_FOLDER:
                if not found_first_standard:
                    # If standard uses inheritance we just use the first docstring
                    standard_info["docstring"] = child.__doc__
                    found_first_standard = True
                standard_info["fields"].update(fields)
            else:
                extra_info["fields"].update(fields)

        return standard_info, extra_info