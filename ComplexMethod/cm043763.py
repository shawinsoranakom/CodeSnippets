def get_components_metadata(self, taxonomy: str, year: int) -> list[dict[str, Any]]:
        """Get component listing with rich metadata.

        Returns a list of dicts suitable for direct output, with keys:
        name, label, description, category, url.

        Handles three enrichment strategies:
        1. FASB (us-gaap, srt): role IDs match component names directly
        2. IFRS: fetch each standard's role file + known names dictionary
        3. SEC multi-component: fetch roles from main schema and match by
           cross-referencing which roles appear in each component's
           presentation file
        """
        # pylint: disable=import-outside-toplevel
        import re

        config = TAXONOMIES.get(taxonomy)

        if not config:
            return []

        components = self.list_available_components(taxonomy, year)

        if not components:
            return []

        # --- Strategy 1: FASB --- role IDs match component names ---
        if config.style == TaxonomyStyle.FASB_STANDARD:
            roles = self._get_roles_for_taxonomy(taxonomy, year)
            role_by_name: dict[str, dict[str, Any]] = {r["name"]: r for r in roles}
            results: list[dict[str, Any]] = []

            # Industry prefix labels for early years (e.g. 2011) where
            # component names carry an industry prefix like "basi-", "bd-",
            # "ci-", "ins-", "re-" that does NOT appear in the role names.
            _industry_prefixes: dict[str, str] = {
                "basi": "Basic",
                "bd": "Broker-Dealer",
                "ci": "Commercial & Industrial",
                "ins": "Insurance",
                "re": "Real Estate",
            }

            for comp in components:
                role = role_by_name.get(comp)
                prefix_label = ""

                # If no direct match, try stripping the first segment as an
                # industry prefix (e.g. "basi-com" -> "com").
                if role is None and "-" in comp:
                    prefix, rest = comp.split("-", 1)
                    role = role_by_name.get(rest)
                    if role is not None:
                        prefix_label = _industry_prefixes.get(prefix, prefix.upper())

                if role:
                    short = role.get("short_name", comp)
                    label = f"{short} ({prefix_label})" if prefix_label else short
                    results.append(
                        {
                            "name": comp,
                            "label": label,
                            "description": role.get("long_name"),
                            "category": role.get("group"),
                            "url": None,
                        }
                    )
                else:
                    results.append(
                        {
                            "name": comp,
                            "label": comp,
                            "description": None,
                            "category": None,
                            "url": None,
                        }
                    )

            return results

        # --- Strategy 2: IFRS — per-standard role files + known names ---
        if config.style == TaxonomyStyle.EXTERNAL and taxonomy == "ifrs":
            date = get_ifrs_version_dates().get(year)
            results = []

            for comp in components:
                label = IFRS_STANDARD_NAMES.get(comp, comp.replace("_", " ").upper())
                description = None
                category = None

                # Try to fetch the role file for this standard
                if date:
                    role_url = (
                        f"https://xbrl.ifrs.org/taxonomy/{date}"
                        f"/full_ifrs/linkbases/{comp}/rol_{comp}_{date}.xsd"
                    )
                    try:
                        content = self.client.fetch_file(role_url)
                        _, roles_list, _, _ = self.parser.parse_schema(content)

                        if roles_list:
                            # Use the first role's definition as description
                            descriptions = [r.get("long_name", "") for r in roles_list]
                            description = "; ".join(d for d in descriptions[:5] if d)
                            # Determine category from definition text
                            first_def = roles_list[0].get("long_name", "")

                            if "Statement" in first_def:
                                category = "statement"
                            elif "Notes" in first_def:
                                category = "notes"
                            else:
                                category = "disclosure"
                    except Exception:  # pylint: disable=broad-except  # noqa: S110
                        pass

                results.append(
                    {
                        "name": comp,
                        "label": label,
                        "description": description or label,
                        "category": category,
                        "url": None,
                    }
                )
            return results

        # --- Strategy 3: SEC multi-component ---
        # Fetch all roles from the main schema, then map roles to components
        # by checking which presentation file uses which role URIs.
        all_roles = self._get_roles_for_taxonomy(taxonomy, year)
        role_by_uri: dict[str, dict[str, Any]] = {}

        for r in all_roles:
            # Build expected role URI patterns
            role_by_uri[r["name"].lower()] = r

        base_url = config.base_url_template.format(year=year)
        results = []

        for comp in components:
            # Try to find which roles this component uses
            comp_roles: list[dict[str, Any]] = []

            # Fetch the component's presentation/schema file to find roleRefs
            comp_urls = []
            found_tc = self.client.find_file(
                base_url, f"{taxonomy}-{comp}-", str(year), ".xsd"
            )
            if found_tc:
                comp_urls.append(found_tc)
            found_c = self.client.find_file(base_url, f"{comp}-{year}", ".xsd")
            if found_c:
                comp_urls.append(found_c)
            if not comp_urls:
                # Broader search: any file containing the component name
                found_broad = self.client.find_file(base_url, comp, str(year), ".xsd")
                if found_broad:
                    comp_urls.append(found_broad)

            for comp_url in comp_urls:
                try:
                    content = self.client.fetch_file(comp_url)
                    resp_text = content.read().decode("utf-8", errors="replace")
                    # Find roleURI references in this file
                    role_uris = re.findall(r'roleURI="([^"]*)"', resp_text)
                    pres_roles = re.findall(
                        r'<link:presentationLink[^>]*role="([^"]*)"',
                        resp_text,
                    )
                    # Match URIs to our known roles
                    used_uris = set(role_uris + pres_roles)

                    for uri in used_uris:
                        # Extract role short name from URI
                        # e.g. http://xbrl.sec.gov/rr/role/RiskReturn -> RiskReturn
                        short = uri.rstrip("/").rsplit("/", 1)[-1]
                        role = role_by_uri.get(short.lower())

                        if role:
                            comp_roles.append(role)

                    if comp_roles:
                        break
                except Exception:  # pylint: disable=broad-except  # noqa: S112
                    continue

            if comp_roles:
                # Sort by document number and show a summary
                comp_roles.sort(key=lambda x: x.get("document_number", "999999"))
                first = comp_roles[0]
                # Build description from all role long names
                description_parts = [r.get("long_name", "") for r in comp_roles]
                results.append(
                    {
                        "name": comp,
                        "label": (
                            first.get("short_name", comp)
                            if len(comp_roles) == 1
                            else f"{comp_roles[0].get('short_name', comp)} (+{len(comp_roles) - 1} more)"
                        ),
                        "description": "; ".join(d for d in description_parts[:5] if d),
                        "category": first.get("group"),
                        "url": None,
                    }
                )
            else:
                # Fallback to known names
                known = SEC_COMPONENT_NAMES.get(taxonomy, {}).get(comp)

                if known:
                    results.append(
                        {
                            "name": comp,
                            "label": known["label"],
                            "description": known.get("description", known["label"]),
                            "category": known.get("category"),
                            "url": None,
                        }
                    )
                else:
                    results.append(
                        {
                            "name": comp,
                            "label": comp.upper(),
                            "description": None,
                            "category": None,
                            "url": None,
                        }
                    )

        return results