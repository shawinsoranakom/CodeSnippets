def adapter(term):
        new_node = parse_xml(f"<div>{term}</div>")
        try:
            for orig_n, new_n in same_struct_iter(orig_node, new_node):
                removed_attrs = [k for k in new_n.attrib if k in MODIFIER_ATTRS and k not in orig_n.attrib]
                for k in removed_attrs:
                    del new_n.attrib[k]
                keep_attrs = {k: v for k, v in orig_n.attrib.items()}
                new_n.attrib.update(keep_attrs)
        except ValueError:  # non-matching structure
            return None

        # remove tags <div> and </div> from result
        return serialize_xml(new_node)[5:-6]