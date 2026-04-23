def _get_ifrs_structure(self, year: int, component: str) -> list[XBRLNode]:
        """Get the parsed IFRS presentation structure for a given component.

        IFRS has a fundamentally different structure from SEC/FASB taxonomies:
        - Hosted on ``xbrl.ifrs.org`` with date-based versioning
        - Presentation linkbases are split across 50+ per-standard XML files
        - A single entry-point XSD references all files

        For a specific standard component (e.g. ``ias_1``, ``ifrs_7``):
            Fetches that standard's presentation linkbase files and builds
            the presentation hierarchy.

        For ``standard`` or any unrecognised component:
            Falls back to the core XSD's flat element list (5000+ elements).

        Parameters
        ----------
        year : int
            The taxonomy year (e.g. 2025).
        component : str
            An IFRS standard identifier (``ias_1``, ``ifrs_7``, …),
            or ``"standard"`` for the full flat element list.

        Returns
        -------
        list[XBRLNode]
            Hierarchical presentation tree (for a specific standard) or
            flat element list (for ``standard``).
        """
        # pylint: disable=import-outside-toplevel
        import re
        from urllib.parse import urljoin

        ifrs_dates = get_ifrs_version_dates()
        date = ifrs_dates.get(year)
        if not date:
            raise OpenBBError(
                f"IFRS taxonomy not available for year {year}. "
                f"Known years: {sorted(ifrs_dates.keys(), reverse=True)}"
            )

        # For a specific standard, fetch its presentation linkbase files
        if component != "standard":
            ep_url = _resolve_ifrs_url(year, f"full_ifrs_entry_point_{date}.xsd")
            try:
                ep_content = self.client.fetch_file(ep_url)
                ep_text = ep_content.read().decode("utf-8", errors="replace")
            except Exception as e:
                raise OpenBBError(
                    f"Failed to fetch IFRS entry point for {year}: {e}"
                ) from e

            # Find all presentationLinkbaseRef hrefs for this standard
            # e.g. full_ifrs/linkbases/ias_1/pre_ias_1_2025-03-27_role-210000.xml
            pres_pattern = re.compile(
                rf'href="(full_ifrs/linkbases/{re.escape(component)}/pre_[^"]+\.xml)"'
            )
            pres_hrefs = pres_pattern.findall(ep_text)

            # Also include dimension presentation files if this is the
            # dimensions component or if specifically requested
            if not pres_hrefs:
                # Try dimension presentations
                dim_pattern = re.compile(
                    r'href="(full_ifrs/dimensions/pre_[^"]+\.xml)"'
                )
                pres_hrefs = dim_pattern.findall(ep_text)

            all_nodes: list[XBRLNode] = []
            for href in pres_hrefs:
                full_url = urljoin(ep_url, href)
                try:
                    content = self.client.fetch_file(full_url)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        nodes = self.parser.parse_presentation(
                            content, TaxonomyStyle.FASB_STANDARD
                        )
                    all_nodes.extend(nodes)
                except Exception:  # pylint: disable=broad-except  # noqa: S112
                    continue

            if all_nodes:
                return all_nodes

        # Fallback: flat element list from the core XSD
        core_url = _resolve_ifrs_url(year, f"full_ifrs/full_ifrs-cor_{date}.xsd")
        try:
            core_content = self.client.fetch_file(core_url)
            return self.parser.parse_schema_elements(core_content)
        except Exception as e:
            raise OpenBBError(
                f"Failed to fetch IFRS core schema for {year}: {e}"
            ) from e