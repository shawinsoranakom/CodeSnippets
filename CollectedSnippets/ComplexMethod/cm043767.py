def get_structure(self, taxonomy: str, year: int, component: str) -> list[XBRLNode]:
        """Get the parsed presentation structure of a taxonomy component.

        Parameters
        ----------
        taxonomy : str
            The taxonomy key (e.g., 'us-gaap', 'dei', 'ecd', 'cyd').
        year : int
            The year of the taxonomy (e.g., 2024).
        component : str
            The component to retrieve (e.g., 'soi', 'bs' for us-gaap,
            'standard' for dei/ecd/cyd, 'rr'/'sr' for oef, 'n3'/'n4'/'n6' for vip).

        Returns
        -------
        list[XBRLNode]
            A list of XBRLNode objects representing the hierarchical
            presentation structure of the component.
        """
        # pylint: disable=import-outside-toplevel

        config = TAXONOMIES.get(taxonomy)
        if not config:
            raise ValueError(
                f"Unsupported taxonomy: {taxonomy}. "
                f"Available: {', '.join(sorted(TAXONOMIES.keys()))}"
            )

        self._ensure_labels(taxonomy, year)
        self._ensure_element_properties(taxonomy, year)

        # FASB taxonomies reference elements from srt, dei, country, and currency;
        # load those labels and properties as well so cross-taxonomy references resolve.
        if config.style == TaxonomyStyle.FASB_STANDARD:
            for dep in ("srt", "dei", "country", "currency"):
                if dep in TAXONOMIES:
                    self._ensure_labels(dep, year)
                    self._ensure_element_properties(dep, year)

        # HMRC DPL references elements from FRC core (core_* namespace);
        # load FRC core labels so cross-taxonomy references resolve.
        if taxonomy == "hmrc-dpl":
            self._load_frc_core_labels(year)

        # --- IFRS: per-standard or flat-element structure ---
        if config.style == TaxonomyStyle.EXTERNAL and taxonomy == "ifrs":
            return self._get_ifrs_structure(year, component)

        # --- Determine the URL to fetch ---

        if config.style == TaxonomyStyle.STATIC:
            full_url = config.base_url_template + config.presentation_file_template
        elif (
            config.style == TaxonomyStyle.EXTERNAL and config.presentation_file_template
        ):
            # EXTERNAL taxonomies with known presentation templates
            # (e.g. HMRC DPL) — use template URL directly, no directory listing.
            base_url = config.base_url_template.format(year=year)
            full_url = base_url + config.presentation_file_template.format(year=year)
        elif config.style == TaxonomyStyle.FASB_STANDARD:
            base_url = config.base_url_template.format(year=year)
            stm_url = f"{base_url}stm/"
            # Resolve actual filename from directory listing — try
            # progressively broader fragment sets to handle different
            # naming conventions across years.
            found = (
                self.client.find_file(
                    stm_url,
                    f"{taxonomy}-stm-{component}-pre-",
                    str(year),
                )
                or self.client.find_file(
                    stm_url,
                    component,
                    "-pre-",
                    str(year),
                )
                or self.client.find_file(
                    stm_url,
                    component,
                    "pre",
                    str(year),
                )
            )
            if not found:
                raise OpenBBError(
                    f"No presentation file found for {taxonomy}/{year}/{component}. "
                    f"Available files in stm/: {[f for f in self.client.list_files(stm_url) if component in f]}"
                )
            full_url = found
        elif component == "standard" and config.style in (
            TaxonomyStyle.SEC_EMBEDDED,
            TaxonomyStyle.SEC_STANDALONE,
        ):
            # For "standard" SEC components, use the *-entire-{year}.xsd
            # which contains (or imports) the full presentation hierarchy.
            # _parse_entire_file handles both direct-embed and import-wrapper.
            try:
                nodes = self._parse_entire_file(taxonomy, year, config)
                if nodes:
                    return nodes
            except Exception:  # pylint: disable=broad-except  # noqa: S110
                pass

            # Fall back to the main schema and flat element extraction
            # (reference taxonomies: country, currency, exch, etc.)
            base_url = config.base_url_template.format(year=year)
            found = self.client.find_file(
                base_url, f"{taxonomy}-{year}", ".xsd"
            ) or self.client.find_file(base_url, taxonomy, str(year), ".xsd")
            if not found:
                raise OpenBBError(
                    f"No schema file found for {taxonomy}/{year} in listing."
                )
            full_url = found
        else:
            base_url = config.base_url_template.format(year=year)
            # Resolve actual file from directory listing — try
            # progressively broader fragment sets.
            found = (
                self.client.find_file(
                    base_url,
                    f"{taxonomy}-{component}-",
                    str(year),
                )
                or self.client.find_file(
                    base_url,
                    f"{taxonomy}-{component}-pre-",
                    str(year),
                )
                or self.client.find_file(
                    base_url,
                    component,
                    str(year),
                )
            )
            if not found:
                raise OpenBBError(
                    f"No presentation file found for {taxonomy}/{year}/{component}. "
                    f"Check available components with list_available_components()."
                )
            full_url = found

        try:
            content = self.client.fetch_file(full_url)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                nodes = self.parser.parse_presentation(content, config.style)

            # Flat element fallback for reference/enumeration taxonomies
            # that have no presentation linkbase at all.
            if not nodes and config.style in (
                TaxonomyStyle.SEC_EMBEDDED,
                TaxonomyStyle.SEC_STANDALONE,
            ):
                if full_url.endswith(".xsd"):
                    content.seek(0)
                    nodes = self.parser.parse_schema_elements(content)
                else:
                    base_url = config.base_url_template.format(year=year)
                    found_schema = self.client.find_file(
                        base_url, f"{taxonomy}-{year}", ".xsd"
                    ) or self.client.find_file(base_url, taxonomy, str(year), ".xsd")
                    if found_schema:
                        schema_content = self.client.fetch_file(found_schema)
                        nodes = self.parser.parse_schema_elements(schema_content)

            # Aggregation: if a component is an empty wrapper that only
            # imports sub-schemas (e.g. sbs "sbsef" imports sbsef-cco,
            # sbsef-com, etc.), aggregate from child components.
            if not nodes:
                all_comps = self.list_available_components(taxonomy, year)
                children = [
                    c
                    for c in all_comps
                    if c != component and c.startswith(f"{component}-")
                ]
                if children:
                    for child in children:
                        child_nodes = self.get_structure(taxonomy, year, child)
                        nodes.extend(child_nodes)

            return nodes

        except Exception as e:
            raise OpenBBError(
                f"Failed to get structure for {taxonomy} {year} {component}: {e}"
            ) from e