def _get_roles_for_taxonomy(self, taxonomy: str, year: int) -> list[dict[str, Any]]:
        """Fetch role definitions for a taxonomy to enrich component listings.

        Returns a list of dicts with keys:
        name, short_name, document_number, group, sub_group, long_name.
        """
        config = TAXONOMIES.get(taxonomy)
        if not config:
            return []

        urls: list[str] = []
        if config.style == TaxonomyStyle.FASB_STANDARD:
            base_url = config.base_url_template.format(year=year)
            short = taxonomy.replace("-gaap", "")
            elts_url = f"{base_url}elts/"
            found_roles = self.client.find_file(
                elts_url, f"{short}-roles-", str(year), ".xsd"
            ) or self.client.find_file(elts_url, "roles", str(year), ".xsd")
            if found_roles:
                urls.append(found_roles)
            found_main = self.client.find_file(
                elts_url, f"{taxonomy}-", str(year), ".xsd"
            ) or self.client.find_file(elts_url, taxonomy, str(year), ".xsd")
            if found_main:
                urls.append(found_main)
        elif config.style in (
            TaxonomyStyle.SEC_EMBEDDED,
            TaxonomyStyle.SEC_STANDALONE,
        ):
            base_url = config.base_url_template.format(year=year)
            for frags in [
                (f"{taxonomy}-{year}", ".xsd"),
                (f"{taxonomy}-entire-", str(year), ".xsd"),
                (f"{taxonomy}-sub-", str(year), ".xsd"),
            ]:
                found = self.client.find_file(base_url, *frags)
                if found:
                    urls.append(found)
        elif config.style == TaxonomyStyle.STATIC:
            urls.append(config.base_url_template + config.label_file_pattern)
        elif config.style == TaxonomyStyle.EXTERNAL and taxonomy == "hmrc-dpl":
            base_url = config.base_url_template.format(year=year)
            urls.append(f"{base_url}dpl-{year}.xsd")

        for url in urls:
            try:
                content = self.client.fetch_file(url)
                _, roles, _, _ = self.parser.parse_schema(content)
                if roles:
                    return roles
            except Exception:  # pylint: disable=broad-except  # noqa: S112
                continue
        return []