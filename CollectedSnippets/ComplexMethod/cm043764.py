def _ensure_labels(self, taxonomy: str, year: int):
        """Load labels and documentation for the given taxonomy/year.

        Tries multiple label sources in order of quality:
        1. The configured label_file_pattern (_lab.xsd or _lab.xml)
        2. The *-entire-{year}.xsd file (has standard role/label)
        3. The *-sub-{year}.xsd file (some taxonomies like ecd)
        4. The *_doc.xsd file (has role/documentation labels)
        5. The main *-{year}.xsd file (may have embedded linkbase)

        For FASB taxonomies, also loads the dedicated *-doc-{year}.xml
        documentation file (separate from the label file).
        """
        # pylint: disable=import-outside-toplevel

        if (taxonomy, year) in self._labels_loaded_for:
            return

        config = TAXONOMIES.get(taxonomy)

        if not config:
            return

        # --- IFRS: dedicated label/doc loading ---
        if config.style == TaxonomyStyle.EXTERNAL and taxonomy == "ifrs":
            date = get_ifrs_version_dates().get(year)

            if not date:
                return

            base = f"https://xbrl.ifrs.org/taxonomy/{date}"
            ifrs_label_urls = [
                f"{base}/full_ifrs/labels/lab_full_ifrs-en_{date}.xml",
                f"{base}/full_ifrs/labels/lab_ias_1-en_{date}.xml",
                f"{base}/full_ifrs/labels/doc_full_ifrs-en_{date}.xml",
                f"{base}/full_ifrs/labels/doc_ias_1-en_{date}.xml",
            ]
            loaded_any = False

            for url in ifrs_label_urls:
                try:
                    labels_before = len(self.parser.labels)
                    docs_before = len(self.parser.documentation)
                    content = self.client.fetch_file(url)

                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.parser.parse_label_linkbase(
                            content, TaxonomyStyle.FASB_STANDARD
                        )

                    if (
                        len(self.parser.labels) > labels_before
                        or len(self.parser.documentation) > docs_before
                    ):
                        loaded_any = True
                except Exception:  # pylint: disable=broad-except  # noqa: S112
                    continue

            if loaded_any:
                self._labels_loaded_for.add((taxonomy, year))

            return

        # --- HMRC DPL: use template URL directly (no directory listing) ---
        if config.style == TaxonomyStyle.EXTERNAL and taxonomy == "hmrc-dpl":
            base_url = config.base_url_template.format(year=year)
            label_url = base_url + config.label_file_pattern.format(year=year)
            try:
                content = self.client.fetch_file(label_url)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.parser.parse_label_linkbase(
                        content, TaxonomyStyle.SEC_EMBEDDED
                    )
                if self.parser.labels:
                    self._labels_loaded_for.add((taxonomy, year))
            except Exception:  # pylint: disable=broad-except  # noqa: S110
                pass

            # Also load doc XSD and main schema for fallback labels
            for suffix in [
                f"hmrc-dpl-{year}.xsd",
                f"hmrc-dpl-{year}_doc.xsd",
                f"dpl-{year}.xsd",
            ]:
                try:
                    content = self.client.fetch_file(base_url + suffix)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.parser.parse_label_linkbase(
                            content, TaxonomyStyle.SEC_EMBEDDED
                        )
                except Exception:  # pylint: disable=broad-except  # noqa: S112
                    continue

            return

        # Build list of candidate URLs to try
        urls_to_try: list[str] = []

        if config.style == TaxonomyStyle.STATIC:
            urls_to_try.append(config.base_url_template + config.label_file_pattern)
        else:
            base_url = config.base_url_template.format(year=year)

            # Primary: resolve label file from directory listing
            if config.label_file_pattern:
                if config.style == TaxonomyStyle.FASB_STANDARD:
                    # FASB: labels in elts/ subdir
                    found = self.client.find_file(
                        f"{base_url}elts/", taxonomy, "lab", str(year)
                    ) or self.client.find_file(f"{base_url}elts/", "lab", str(year))
                    if found:
                        urls_to_try.append(found)
                else:
                    # SEC: find the label file (any naming convention)
                    found = self.client.find_file(
                        base_url, taxonomy, "lab", str(year)
                    ) or self.client.find_file(base_url, "lab", str(year))
                    if found:
                        urls_to_try.append(found)

            # Fallbacks for SEC taxonomies
            if config.style != TaxonomyStyle.FASB_STANDARD:
                for frags in [
                    (f"{taxonomy}-{year}", ".xsd"),
                    (f"{taxonomy}-entire-", str(year), ".xsd"),
                    (f"{taxonomy}-sub-", str(year), ".xsd"),
                    (f"{taxonomy}-std-", str(year)),
                    (taxonomy, "doc", str(year)),
                ]:
                    found = self.client.find_file(base_url, *frags)
                    if found:
                        urls_to_try.append(found)

        loaded_any = False

        for url in urls_to_try:
            try:
                labels_before = len(self.parser.labels)
                docs_before = len(self.parser.documentation)
                content = self.client.fetch_file(url)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.parser.parse_label_linkbase(
                        content, TaxonomyStyle.SEC_EMBEDDED
                    )

                if (
                    len(self.parser.labels) > labels_before
                    or len(self.parser.documentation) > docs_before
                ):
                    loaded_any = True
            except Exception:  # pylint: disable=broad-except  # noqa: S112
                continue

        # Load dedicated documentation files (labels and docs are often
        # in separate files).  FASB uses *-doc-{year}.xml; SEC uses
        # *_doc.xsd (already included in urls_to_try above).
        doc_urls: list[str] = []
        if config.style == TaxonomyStyle.FASB_STANDARD:
            base_url = config.base_url_template.format(year=year)
            found_doc = self.client.find_file(
                f"{base_url}elts/", taxonomy, "doc", str(year)
            ) or self.client.find_file(f"{base_url}elts/", "doc", str(year))
            if found_doc:
                doc_urls.append(found_doc)

        for url in doc_urls:
            try:
                docs_before = len(self.parser.documentation)
                content = self.client.fetch_file(url)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.parser.parse_label_linkbase(
                        content, TaxonomyStyle.FASB_STANDARD
                    )

                if len(self.parser.documentation) > docs_before:
                    loaded_any = True
            except Exception:  # pylint: disable=broad-except  # noqa: S112
                continue

        if loaded_any:
            self._labels_loaded_for.add((taxonomy, year))

        # For FASB taxonomies, fallback is not needed — the _lab.xml should work
        if config.style == TaxonomyStyle.FASB_STANDARD and not self.parser.labels:
            warnings.warn(f"Could not load standard labels for {taxonomy} {year}")

        # Reference fallback: SEC taxonomies (CYD, ECD, OEF, SBS, SPAC,
        # SRO, FND, etc.) often have no role/documentation labels but do
        # embed referenceLink elements with regulatory citations.  Parse
        # those as fallback documentation for elements still missing docs.
        if config.style in (
            TaxonomyStyle.SEC_EMBEDDED,
            TaxonomyStyle.SEC_STANDALONE,
        ):
            base_url = config.base_url_template.format(year=year)
            found_ref = self.client.find_file(
                base_url, f"{taxonomy}-{year}", ".xsd"
            ) or self.client.find_file(base_url, taxonomy, "ref", str(year))
            if not found_ref:
                # Broader: any .xsd containing the taxonomy name and year
                found_ref = self.client.find_file(base_url, taxonomy, str(year), ".xsd")
            ref_url = found_ref

            if ref_url:
                try:
                    ref_content = self.client.fetch_file(ref_url)
                    self.parser.parse_reference_linkbase(ref_content)
                except Exception:  # pylint: disable=broad-except  # noqa: S110
                    pass