def list_available_taxonomies(
        self, category: TaxonomyCategory | str | None = None
    ) -> dict[str, dict[str, str]]:
        """List all registered taxonomies with their labels and descriptions.

        Parameters
        ----------
        category : TaxonomyCategory | str | None
            If provided, filter to only taxonomies in this category.
            Accepts a TaxonomyCategory enum or its string value
            (e.g., "operating_company", "investment_company").

        Returns
        -------
        dict[str, dict[str, str]]
            A dictionary mapping taxonomy keys to their metadata
            (label, description, category, style, sec_reference_url).
        """
        cat_filter: TaxonomyCategory | None = None

        if category is not None:
            if isinstance(category, str):
                try:
                    cat_filter = TaxonomyCategory(category)
                except ValueError:
                    valid = [c.value for c in TaxonomyCategory]
                    raise ValueError(
                        f"Invalid category: {category!r}. Valid values: {valid}"
                    ) from None
            else:
                cat_filter = category

        result = {}

        for key, config in TAXONOMIES.items():
            if cat_filter is not None and config.category != cat_filter:
                continue

            result[key] = {
                "label": config.label,
                "description": config.description,
                "category": config.category.value,
                "style": config.style.name,
                "has_label_linkbase": str(config.has_label_linkbase),
                "sec_reference_url": config.sec_reference_url,
            }

        return result