def transform_query(params: dict[str, Any]) -> FredSearchQueryParams:
        """Transform query."""
        transformed_params = params.copy()

        if (
            transformed_params.get("release_id")
            and not transformed_params.get("search_type")
        ) or (
            not transformed_params.get("query")
            and not transformed_params.get("release_id")
            and not transformed_params.get("series_id")
        ):
            transformed_params["search_type"] = "release"
        elif (
            not transformed_params.get("query")
            and (
                transformed_params.get("search_type") in ["full_text", "series_id"]
                or not transformed_params.get("search_type")
            )
            and not transformed_params.get("series_id")
        ):
            raise OpenBBError(
                "A query is required for search_type 'full_text' or 'series_id'."
            )

        if transformed_params.get("exclude_tag_names") and not transformed_params.get(
            "tag_names"
        ):
            raise OpenBBError(
                "Field 'exclude_tag_names' requires 'tag_names' to be set."
            )

        return FredSearchQueryParams.model_validate(transformed_params)