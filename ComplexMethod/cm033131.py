def _get_spine_items(zf):
        """Return content file paths in spine (reading) order."""
        # 1. Find the OPF file path from META-INF/container.xml
        try:
            container_xml = zf.read("META-INF/container.xml")
        except KeyError:
            return RAGFlowEpubParser._fallback_xhtml_order(zf)

        try:
            container_root = ElementTree.fromstring(container_xml)
        except ElementTree.ParseError:
            logger.warning("Failed to parse META-INF/container.xml; falling back to XHTML order.")
            return RAGFlowEpubParser._fallback_xhtml_order(zf)

        rootfile_el = container_root.find(f".//{{{_CONTAINER_NS}}}rootfile")
        if rootfile_el is None:
            return RAGFlowEpubParser._fallback_xhtml_order(zf)

        opf_path = rootfile_el.get("full-path", "")
        if not opf_path:
            return RAGFlowEpubParser._fallback_xhtml_order(zf)

        # Base directory of the OPF file (content paths are relative to it)
        opf_dir = opf_path.rsplit("/", 1)[0] + "/" if "/" in opf_path else ""

        # 2. Parse the OPF file
        try:
            opf_xml = zf.read(opf_path)
        except KeyError:
            return RAGFlowEpubParser._fallback_xhtml_order(zf)

        try:
            opf_root = ElementTree.fromstring(opf_xml)
        except ElementTree.ParseError:
            logger.warning("Failed to parse OPF file '%s'; falling back to XHTML order.", opf_path)
            return RAGFlowEpubParser._fallback_xhtml_order(zf)

        # 3. Build id->href+mediatype map from <manifest>
        manifest = {}
        for item in opf_root.findall(f".//{{{_OPF_NS}}}item"):
            item_id = item.get("id", "")
            href = item.get("href", "")
            media_type = item.get("media-type", "")
            if item_id and href:
                manifest[item_id] = (href, media_type)

        # 4. Walk <spine> to get reading order
        spine_items = []
        for itemref in opf_root.findall(f".//{{{_OPF_NS}}}itemref"):
            idref = itemref.get("idref", "")
            if idref not in manifest:
                continue
            href, media_type = manifest[idref]
            if media_type not in _XHTML_MEDIA_TYPES:
                continue
            spine_items.append(opf_dir + href)

        return (
            spine_items if spine_items else RAGFlowEpubParser._fallback_xhtml_order(zf)
        )