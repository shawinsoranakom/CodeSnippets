def get_choices_for_dim(dim_id: str) -> list:
        """Get available choices for a dimension using constraints API."""
        key = build_key_with_indicator(dim_id)
        constraints = metadata.get_available_constraints(
            dataflow_id=dataflow_id,
            key=key,
            component_id=dim_id,
        )
        # Get labels from params
        labels = {opt["value"]: opt["label"] for opt in params.get(dim_id, [])}
        # Also try to get labels from codelist
        codelist_labels: dict = {}
        dim_meta: dict = next((d for d in sorted_dims if d.get("id") == dim_id), {})

        if dim_meta:
            codelist_id = metadata._resolve_codelist_id(
                dataflow_id, dsd_id, dim_id, dim_meta
            )

            if codelist_id and codelist_id in metadata._codelist_cache:
                codelist_labels = metadata._codelist_cache.get(codelist_id, {})

        choices: list = []

        for kv in constraints.get("key_values", []):
            if kv.get("id") == dim_id:
                for value in kv.get("values", []):
                    # Try params first, then codelist, then fall back to value
                    label = labels.get(value) or codelist_labels.get(value) or value
                    choices.append({"label": label, "value": value})

        return choices