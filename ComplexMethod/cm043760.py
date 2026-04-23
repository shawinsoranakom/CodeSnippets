def parse_instance(
        self,
        file_content: BytesIO,
        base_url: str | None = None,
    ) -> tuple[
        dict[str, dict[str, Any]],
        dict[str, str],
        dict[str, list[dict[str, Any]]],
    ]:
        """Parse an XBRL instance document.

        Parameters
        ----------
        file_content : BytesIO
            The content of the XBRL instance document as a byte stream.
        base_url : str | None
            The base URL of the filing directory (ending with ``/``).
            When provided, the parser automatically discovers and parses
            the filing's label and presentation linkbases to resolve
            human-readable labels and documentation for each fact.

        Returns
        -------
        tuple[dict, dict, dict]
            A tuple containing:
            - contexts: A dictionary mapping context IDs to their details
              (entity, period_type, start, end, and any dimensional qualifiers).
            - units: A dictionary mapping unit IDs to their resolved measure
              strings (e.g., "iso4217:USD", "shares", "iso4217:USD / shares").
            - facts: A dictionary mapping element tags to a list of fact
              instances. Each fact is fully resolved with: tag, label,
              documentation, entity, period_type, start, end, dimensions,
              unit, decimals, value, and a ``presentation`` list describing
              each table appearance (table, parent, order, preferred_label).
        """
        try:
            root = self._get_xml_root(file_content)

            if root is None:
                raise ValueError("Failed to parse XML instance document: root is None")

            xbrli_ns = "http://www.xbrl.org/2003/instance"
            xbrldi_ns = "http://xbrl.org/2006/xbrldi"

            # Build namespace prefix map from xmlns declarations for
            # accurate tag normalization (handles company extensions, SEC
            # taxonomies like ecd, country, etc.)
            file_content.seek(0)
            ns_prefix_map = self._build_ns_prefix_map(file_content.read())

            contexts: dict[str, dict[str, Any]] = {}
            facts: dict[str, list[dict[str, Any]]] = {}

            # Parse unit definitions first so we can resolve unitRef in facts
            units = self._parse_units(root)

            # Load filing-level labels and presentation hierarchy
            labels_map: dict[str, dict[str, str]] = {}
            presentation_map: dict[str, list[dict[str, Any]]] = {}
            if base_url is not None:
                labels_map, presentation_map = self._parse_filing_labels(root, base_url)

            # Parse contexts - extract entity, period, and dimensions
            for context in root.findall(f".//{{{xbrli_ns}}}context"):
                context_id = context.get("id")
                if not context_id:
                    continue

                ctx_data: dict[str, Any] = {}

                # Entity identifier (CIK)
                entity = context.find(f"{{{xbrli_ns}}}entity")
                if entity is not None:
                    identifier = entity.find(f"{{{xbrli_ns}}}identifier")
                    if identifier is not None and identifier.text:
                        ctx_data["entity"] = identifier.text.strip()

                # Period
                period = context.find(f"{{{xbrli_ns}}}period")
                if period is not None:
                    instant = period.find(f"{{{xbrli_ns}}}instant")
                    start_date = period.find(f"{{{xbrli_ns}}}startDate")
                    end_date = period.find(f"{{{xbrli_ns}}}endDate")
                    forever = period.find(f"{{{xbrli_ns}}}forever")

                    if instant is not None:
                        ctx_data["period_type"] = "instant"
                        ctx_data["start"] = None
                        ctx_data["end"] = instant.text
                    elif forever is not None:
                        ctx_data["period_type"] = "forever"
                        ctx_data["start"] = None
                        ctx_data["end"] = None
                    else:
                        ctx_data["period_type"] = "duration"
                        ctx_data["start"] = (
                            start_date.text if start_date is not None else None
                        )
                        ctx_data["end"] = (
                            end_date.text if end_date is not None else None
                        )

                # Dimensions from segment (most common) or scenario
                dimensions: dict[str, str] = {}
                segment = (
                    entity.find(f"{{{xbrli_ns}}}segment")
                    if entity is not None
                    else None
                )
                scenario = context.find(f"{{{xbrli_ns}}}scenario")

                for container in (segment, scenario):
                    if container is None:
                        continue
                    # Explicit dimensions: <xbrldi:explicitMember dimension="axis">member</xbrldi:explicitMember>
                    for explicit in container.findall(f"{{{xbrldi_ns}}}explicitMember"):
                        dim = explicit.get("dimension", "")
                        val = (explicit.text or "").strip()
                        if dim and val:
                            dimensions[dim] = val
                    # Typed dimensions
                    # <xbrldi:typedMember dimension="axis"><ns:value>text</ns:value></xbrldi:typedMember>
                    for typed in container.findall(f"{{{xbrldi_ns}}}typedMember"):
                        dim = typed.get("dimension", "")
                        if dim:
                            for child in typed:
                                child_tag = (
                                    child.tag.split("}")[-1]
                                    if "}" in child.tag
                                    else child.tag
                                )
                                dimensions[dim] = (
                                    f"{child_tag}:{child.text}"
                                    if child.text
                                    else child_tag
                                )

                if dimensions:
                    ctx_data["dimensions"] = dimensions

                contexts[context_id] = ctx_data

            # Parse facts - iterate all elements and extract those with contextRef
            for elem in root.iter():
                context_ref = elem.get("contextRef")
                if context_ref is None:
                    continue

                # Get the tag name, normalizing namespace URI to prefix
                tag = elem.tag

                if "}" in tag:
                    ns, local = tag.rsplit("}", 1)
                    ns = ns[1:]  # Remove leading {
                    prefix = self._resolve_ns_prefix(ns, ns_prefix_map)
                    tag = f"{prefix}_{local}"
                else:
                    tag = tag.replace(":", "_")

                # Resolve unitRef to actual measure string
                unit_ref = elem.get("unitRef")
                resolved_unit = units.get(unit_ref, unit_ref) if unit_ref else None

                # Resolve context_ref to inline period/entity/dimensions
                ctx = contexts.get(context_ref, {})

                # Resolve labels from the filing's label linkbase
                elem_labels = labels_map.get(tag, {})
                label = elem_labels.get("label") or tag
                documentation = elem_labels.get("documentation")

                # Presentation metadata (table, parent, order, preferred_label)
                pres_entries = presentation_map.get(tag)

                fact_data: dict[str, Any] = {
                    "tag": tag,
                    "label": label,
                    "documentation": documentation,
                    "context_ref": context_ref,
                    "fact_id": elem.get("id"),
                    "entity": ctx.get("entity"),
                    "period_type": ctx.get("period_type"),
                    "start": ctx.get("start"),
                    "end": ctx.get("end"),
                    "unit": resolved_unit,
                    "decimals": elem.get("decimals"),
                    "value": elem.text,
                }

                # Only include dimensions key if present; resolve member labels
                dims = ctx.get("dimensions")

                if dims:
                    resolved_dims: dict[str, dict[str, Any]] = {}

                    for axis, member in dims.items():
                        # Normalize member to underscore format for label lookup
                        member_key = member.replace(":", "_")
                        member_labels = labels_map.get(member_key, {})
                        member_label = member_labels.get("label", member)
                        resolved_dims[axis] = {
                            "member": member,
                            "label": member_label,
                        }

                    fact_data["dimensions"] = resolved_dims

                if pres_entries:
                    fact_data["presentation"] = pres_entries

                if tag not in facts:
                    facts[tag] = []

                facts[tag].append(fact_data)

            return contexts, units, facts

        except Exception as e:
            raise OpenBBError(f"Failed to parse instance document: {e}") from e