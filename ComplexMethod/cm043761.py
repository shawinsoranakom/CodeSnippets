def _ensure_element_properties(self, taxonomy: str, year: int):
        """Load element properties (type, periodType, balance, etc.) for a taxonomy.

        Fetches the main schema XSD for the taxonomy and extracts element
        attributes into ``self.parser.element_properties``.
        """
        if (taxonomy, year) in self._properties_loaded_for:
            return

        config = TAXONOMIES.get(taxonomy)
        if not config:
            return

        urls: list[str] = []

        if config.style == TaxonomyStyle.EXTERNAL and taxonomy == "ifrs":
            date = get_ifrs_version_dates().get(year)
            if date:
                urls.append(
                    f"https://xbrl.ifrs.org/taxonomy/{date}"
                    f"/full_ifrs/full_ifrs-cor_{date}.xsd"
                )
        elif config.style == TaxonomyStyle.EXTERNAL and taxonomy == "hmrc-dpl":
            base_url = config.base_url_template.format(year=year)
            urls.append(f"{base_url}dpl-{year}.xsd")
        elif config.style == TaxonomyStyle.STATIC:
            urls.append(config.base_url_template + config.label_file_pattern)
        else:
            base_url = config.base_url_template.format(year=year)
            if config.style == TaxonomyStyle.FASB_STANDARD:
                elts_url = f"{base_url}elts/"
                found = self.client.find_file(
                    elts_url, f"{taxonomy}-", str(year), ".xsd"
                ) or self.client.find_file(elts_url, taxonomy, str(year), ".xsd")
                if found:
                    urls.append(found)
            else:
                for frags in [
                    (f"{taxonomy}-", str(year), ".xsd"),
                    (f"{taxonomy}-entire-", str(year), ".xsd"),
                    (taxonomy, str(year), ".xsd"),
                ]:
                    found = self.client.find_file(base_url, *frags)
                    if found:
                        urls.append(found)

        for url in urls:
            try:
                content = self.client.fetch_file(url)
                loaded = self.parser.load_schema_element_properties(content)
                if loaded > 0:
                    self._properties_loaded_for.add((taxonomy, year))
                    return
            except Exception:  # pylint: disable=broad-except  # noqa: S112
                continue