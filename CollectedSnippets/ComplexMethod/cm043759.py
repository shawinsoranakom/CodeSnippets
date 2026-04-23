def _parse_filing_labels(self, root: Element, base_url: str) -> tuple[
        dict[str, dict[str, str]],
        dict[str, list[dict[str, Any]]],
    ]:
        """Discover and parse label/presentation linkbases from a filing.

        Follows the instance document's schemaRef → company schema →
        linkbaseRef chain to find and parse the label and presentation
        linkbase files for the filing.

        Parameters
        ----------
        root : Element
            The parsed root element of the XBRL instance document.
        base_url : str
            The base URL of the filing directory (ending with ``/``),
            used to resolve relative linkbase references.

        Returns
        -------
        tuple[dict[str, dict[str, str]], dict[str, list[dict[str, Any]]]]
            - labels_map: element_id → dict of role_short → label_text.
              Roles include ``label``, ``terseLabel``, ``totalLabel``,
              ``negatedLabel``, ``verboseLabel``, ``periodStartLabel``,
              ``periodEndLabel``, ``documentation``, etc.
            - presentation_map: element_id → list of dicts, each with
              ``table`` (role short name), ``parent`` (parent element_id),
              ``order`` (float), and ``preferred_label`` (role short name).
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import make_request
        from openbb_sec.utils.definitions import HEADERS as SEC_HEADERS

        link_ns = "http://www.xbrl.org/2003/linkbase"
        xlink_ns = "http://www.w3.org/1999/xlink"
        labels_map: dict[str, dict[str, str]] = {}
        presentation_map: dict[str, list[dict[str, Any]]] = {}
        # 1. Find schemaRef in instance document
        schema_href = None

        for ref in root.findall(f".//{{{link_ns}}}schemaRef"):
            schema_href = ref.get(f"{{{xlink_ns}}}href")

            if schema_href:
                break

        if not schema_href:
            return labels_map, presentation_map

        # Resolve schema URL (may be relative)
        from urllib.parse import urljoin  # pylint: disable=import-outside-toplevel

        schema_url = (
            schema_href
            if schema_href.startswith("http")
            else urljoin(base_url, schema_href)
        )

        # 2. Fetch company schema and find linkbaseRef entries
        try:
            schema_resp = make_request(schema_url, headers=SEC_HEADERS)
            schema_resp.raise_for_status()
            schema_root = self._get_xml_root(BytesIO(schema_resp.content))

            if schema_root is None:
                return labels_map, presentation_map

        except Exception:  # pylint: disable=broad-except  # noqa: S112
            return labels_map, presentation_map

        label_url = None
        pre_url = None

        for ref in schema_root.findall(f".//{{{link_ns}}}linkbaseRef"):
            role = ref.get(f"{{{xlink_ns}}}role", "")
            href = ref.get(f"{{{xlink_ns}}}href", "")

            if not href:
                continue
            full_url = href if href.startswith("http") else urljoin(schema_url, href)

            if "labelLinkbaseRef" in role or "labelLinkbase" in role:
                label_url = full_url
            elif "presentationLinkbaseRef" in role or "presentationLinkbase" in role:
                pre_url = full_url

        # 3. Parse label linkbase
        if label_url:
            try:
                lab_resp = make_request(label_url, headers=SEC_HEADERS)
                lab_resp.raise_for_status()
                lab_root = self._get_xml_root(BytesIO(lab_resp.content))

                if lab_root is not None:
                    # Build loc_map: xlink:label -> element_id
                    loc_map: dict[str, str] = {}

                    for loc in lab_root.findall(f".//{{{link_ns}}}loc"):
                        href = loc.get(f"{{{xlink_ns}}}href", "")
                        loc_label = loc.get(f"{{{xlink_ns}}}label", "")

                        if href and "#" in href:
                            loc_map[loc_label] = href.split("#")[1]

                    # Build resource_map: xlink:label -> {role_short: text}
                    resource_map: dict[str, dict[str, str]] = {}

                    for res in lab_root.findall(f".//{{{link_ns}}}label"):
                        role = res.get(f"{{{xlink_ns}}}role", "")
                        role_short = role.split("/")[-1] if role else "label"
                        res_label = res.get(f"{{{xlink_ns}}}label", "")

                        if res_label not in resource_map:
                            resource_map[res_label] = {}

                        resource_map[res_label][role_short] = res.text or ""

                    # Follow arcs to connect elements to labels
                    for arc in lab_root.findall(f".//{{{link_ns}}}labelArc"):
                        from_loc = arc.get(f"{{{xlink_ns}}}from", "")
                        to_label = arc.get(f"{{{xlink_ns}}}to", "")

                        if from_loc in loc_map and to_label in resource_map:
                            elem_id = loc_map[from_loc]

                            if elem_id not in labels_map:
                                labels_map[elem_id] = {}

                            labels_map[elem_id].update(resource_map[to_label])
            except Exception:  # pylint: disable=broad-except  # noqa: S110
                pass

        # 4. Parse presentation linkbase for hierarchy, order, and preferred labels
        if pre_url:
            try:
                pre_resp = make_request(pre_url, headers=SEC_HEADERS)
                pre_resp.raise_for_status()
                pre_root = self._get_xml_root(BytesIO(pre_resp.content))
                if pre_root is not None:
                    # Process each presentationLink (table/role) separately
                    for plink in pre_root.findall(f".//{{{link_ns}}}presentationLink"):
                        role = plink.get(f"{{{xlink_ns}}}role", "")
                        role_short = role.split("/")[-1] if role else ""

                        # Build loc_map for this role
                        pre_loc_map: dict[str, str] = {}
                        for loc in plink.findall(f"{{{link_ns}}}loc"):
                            href = loc.get(f"{{{xlink_ns}}}href", "")
                            loc_label = loc.get(f"{{{xlink_ns}}}label", "")
                            if href and "#" in href:
                                pre_loc_map[loc_label] = href.split("#")[1]

                        # Extract parent, order, and preferred label from arcs
                        for arc in plink.findall(f"{{{link_ns}}}presentationArc"):
                            from_loc = arc.get(f"{{{xlink_ns}}}from", "")
                            to_loc = arc.get(f"{{{xlink_ns}}}to", "")
                            order = arc.get("order")
                            pref = arc.get("preferredLabel", "")

                            parent_id = pre_loc_map.get(from_loc)
                            child_id = pre_loc_map.get(to_loc)

                            if child_id is not None:
                                entry: dict[str, Any] = {
                                    "table": role_short,
                                    "parent": parent_id,
                                    "order": (float(order) if order else None),
                                    "preferred_label": (
                                        pref.split("/")[-1] if pref else None
                                    ),
                                }
                                if child_id not in presentation_map:
                                    presentation_map[child_id] = []
                                presentation_map[child_id].append(entry)
            except Exception:  # pylint: disable=broad-except  # noqa: S110
                pass

        return labels_map, presentation_map