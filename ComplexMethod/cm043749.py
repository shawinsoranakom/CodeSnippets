def get_components_for_year(self, year: int, config: TaxonomyConfig) -> list[str]:
        """Discovery of available components (statements/disclosures).

        For FASB_STANDARD taxonomies, scans the stm/ directory for presentation files.
        For SEC_EMBEDDED/SEC_STANDALONE taxonomies, scans the root directory.
        For EXTERNAL (IFRS), parses the entry-point XSD for standard sub-schemas.
        For STATIC taxonomies, returns a fixed list.
        """
        # pylint: disable=import-outside-toplevel
        import re

        if config.style == TaxonomyStyle.STATIC:
            return ["standard"]

        if config.style == TaxonomyStyle.EXTERNAL:
            # IFRS: Parse entry-point XSD to discover per-standard components
            if "ifrs" in config.base_url_template:
                try:
                    ep_url = _resolve_ifrs_url(
                        year,
                        f"full_ifrs_entry_point_{get_ifrs_version_dates()[year]}.xsd",
                    )
                    content = self._fetch_url_content(ep_url)
                    # Extract standard names from schemaLocation imports
                    # e.g. full_ifrs/linkbases/ias_1/rol_ias_1_2025-03-27.xsd
                    pattern = r"full_ifrs/linkbases/([a-z]+_\d+)/rol_"
                    standards = sorted(set(re.findall(pattern, content)))
                    return standards if standards else ["standard"]
                except Exception as e:
                    raise OpenBBError(
                        f"Failed to fetch IFRS components for {year}: {e}"
                    ) from e
            # Non-IFRS external taxonomies (e.g. HMRC DPL): single component
            return ["standard"]

        base_url = config.base_url_template.format(year=year)

        if config.style == TaxonomyStyle.FASB_STANDARD:
            stm_url = f"{base_url}stm/"
            try:
                files = self.list_files(stm_url)
                # Extract component names from actual presentation filenames.
                # Files look like: us-gaap-stm-{comp}-pre-{date}.xml
                components: set[str] = set()
                prefix = config.presentation_file_template.split("{name}")[0]
                # e.g. "stm/us-gaap-stm-" → we strip "stm/" to get "us-gaap-stm-"
                if prefix.startswith("stm/"):
                    prefix = prefix[4:]
                for fname in files:
                    if "-pre-" in fname and fname.startswith(prefix):
                        rest = fname[len(prefix) :]
                        # rest = "soc-pre-2023.xml" or "soc-pre-2019-01-31.xml"
                        comp = rest.split("-pre-")[0]
                        if comp:
                            components.add(comp)
                return sorted(components)
            except Exception as e:
                raise OpenBBError(f"Failed to fetch components for {year}: {e}") from e

        if config.style in (
            TaxonomyStyle.SEC_EMBEDDED,
            TaxonomyStyle.SEC_STANDALONE,
        ):
            try:
                files = self.list_files(base_url)
                # Extract component names from actual presentation / sub-schema files.
                # Use the regex to pull component names out of real filenames.
                components: set[str] = set()  # type: ignore[no-redef]
                for fname in files:
                    # Try the configured regex (replace {year} with a catch-all date pattern)
                    if config.presentation_pattern_regex:
                        yr_pat = rf"{year}(?:-\d{{2}}-\d{{2}})?"
                        pattern = config.presentation_pattern_regex.format(
                            year=yr_pat,
                        )
                        m = re.match(pattern, fname)
                        if m:
                            components.add(m.group(1))
                if components:
                    return sorted(components)
                # Fallback: if any file mentions this year, it's a single-component taxonomy
                if any(str(year) in f for f in files):
                    return ["standard"]
                return []
            except Exception:
                return []

        return []