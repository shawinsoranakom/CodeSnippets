def _parse_entire_file(
        self, taxonomy: str, year: int, config: TaxonomyConfig
    ) -> list[XBRLNode]:
        """Parse a taxonomy's *-entire-{year}.xsd, following xs:import if needed.

        SEC taxonomies publish an ``-entire-`` XSD that either:
        1. Embeds presentation, label, and definition linkbases directly
           (cyd, vip, country, currency, exch, naics, sic, stpr), or
        2. Acts as an import wrapper referencing ``-sub-``, ``-pre-``, or
           component XSDs that contain the actual linkbases (ecd, ffd, rxp,
           spac, cef, oef, fnd, sro, sbs, snj).

        This method handles both cases by first trying direct parsing, then
        resolving local imports and aggregating their presentation trees.

        Parameters
        ----------
        taxonomy : str
            The taxonomy key (e.g. ``'cyd'``, ``'ecd'``).
        year : int
            The taxonomy year.
        config : TaxonomyConfig
            The taxonomy's configuration.

        Returns
        -------
        list[XBRLNode]
            Parsed presentation tree, or empty list if the ``-entire-`` file
            is not available.
        """
        from urllib.parse import urljoin  # pylint: disable=import-outside-toplevel

        base_url = config.base_url_template.format(year=year)
        found = self.client.find_file(
            base_url, f"{taxonomy}-entire-", str(year), ".xsd"
        )
        if not found:
            return []  # No -entire- file in the directory listing
        entire_url = found

        try:
            content = self.client.fetch_file(entire_url)
        except Exception:
            return []  # No -entire- file available

        # Try direct parse (works when linkbases are embedded directly)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            nodes = self.parser.parse_presentation(content, config.style)
        if nodes:
            return nodes

        # Direct parse returned nothing — follow xs:import references.
        content.seek(0)
        _, _, _, imports = self.parser.parse_schema(content)

        all_nodes: list[XBRLNode] = []
        for imp in imports:
            loc = imp.get("schemaLocation", "")
            # Only follow local imports (not external XBRL/FASB specs)
            if loc.startswith("http") or not loc:
                continue
            import_url = urljoin(entire_url, loc)
            try:
                sub_content = self.client.fetch_file(import_url)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    sub_nodes = self.parser.parse_presentation(
                        sub_content, config.style
                    )
                all_nodes.extend(sub_nodes)
            except Exception:  # pylint: disable=broad-except  # noqa: S112
                continue
        return all_nodes