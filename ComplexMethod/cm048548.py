def _rebuild_xml_with_sorted_namespaces(cls, root: etree._Element) -> etree._Element:
        # Collect all namespaces and prefixes
        all_nsmap = {
            prefix: uri
            for elem in root.iter()
            for prefix, uri in elem.nsmap.items()
        }

        # Sort all namespaces
        nsmap_str_keys = [key for key in all_nsmap if isinstance(key, str)]
        sorted_nsmap_keys = [
            *((None,) if None in all_nsmap else ()),
            *sorted(nsmap_str_keys),
        ]
        sorted_nsmap = {
            nsmap_key: all_nsmap[nsmap_key]
            for nsmap_key in sorted_nsmap_keys
        }

        # Build a new root element with the sorted namespaces and all original root attrib & children
        new_root = etree.Element(root.tag, nsmap=sorted_nsmap)
        new_root.text = root.text
        for attrib_key, attrib_val in root.attrib.items():
            new_root.attrib[attrib_key] = attrib_val
        for child in root.getchildren():
            new_root.append(child)

        return new_root