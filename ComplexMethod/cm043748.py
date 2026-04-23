def get_available_years(self, taxonomy: str, config: TaxonomyConfig) -> list[int]:
        """Scrapes the base directory to find available taxonomy years."""
        # pylint: disable=import-outside-toplevel
        import re

        if config.style == TaxonomyStyle.STATIC:
            # Static taxonomies (e.g., rocr 2015) embed the year in the URL.
            m = re.search(r"/(\d{4})/", config.base_url_template)
            return [int(m.group(1))] if m else []

        if config.style == TaxonomyStyle.EXTERNAL:
            # IFRS uses date-based versioning; discover from edgartaxonomies.xml
            if taxonomy == "ifrs":
                return sorted(get_ifrs_version_dates().keys(), reverse=True)
            # HMRC DPL: no directory listing, hardcoded known years
            if taxonomy == "hmrc-dpl":
                return list(_HMRC_DPL_YEARS)
            return []

        base_root = config.base_url_template.split("{year}")[0]

        try:
            content = self._fetch_url_content(base_root)
            years = re.findall(r'href="(\d{4})/"', content)
            return sorted([int(y) for y in years], reverse=True)
        except Exception as e:
            raise OpenBBError(
                f"Failed to fetch available years for {taxonomy}: {e}"
            ) from e