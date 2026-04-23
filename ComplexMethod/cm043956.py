def _build_translation_maps(self, structure: dict, dataflow: str) -> dict:
        """Build dimension translation maps from the response structure values.
        Fallback to metadata.get_dataflow_parameters if a dimension has no inline values.
        Returns a mapping: { dimension_id: { code: label, ... }, ... }
        """
        maps: dict = {}

        # First, get ALL translations from cached dataflow parameters
        try:
            df_params = self.metadata.get_dataflow_parameters(dataflow)
            for dim_id, options in df_params.items():
                if isinstance(options, list) and options:
                    maps[dim_id] = {
                        opt["value"]: opt["label"] for opt in options if "value" in opt
                    }
        except Exception:  # noqa  # pylint: disable=broad-except
            pass

        # Then overlay with any labels from the structure (if they're better than codes)
        for dim_group in ("series", "observation"):
            for dim in structure.get("dimensions", {}).get(dim_group, []):
                dim_id = dim.get("id")

                if not dim_id:
                    continue

                vals = dim.get("values", [])

                if not vals:
                    continue

                # Only update if the structure has actual names (not just codes)
                for v in vals:
                    code = v.get("id")
                    name = v.get("name")
                    # Only use if name is different from code
                    if code and name and name != code:
                        if dim_id not in maps:
                            maps[dim_id] = {}
                        maps[dim_id][code] = name

        return maps