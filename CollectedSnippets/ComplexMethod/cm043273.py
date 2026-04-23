def remove_unwanted_attributes_fast(
        self, root: lhtml.HtmlElement, important_attrs=None, keep_data_attributes=False
    ) -> lhtml.HtmlElement:
        """
        Removes all attributes from each element (including root) except those in `important_attrs`.
        If `keep_data_attributes=True`, also retain any attribute starting with 'data-'.

        Returns the same root element, mutated in-place, for fluent usage.
        """
        if important_attrs is None:
            important_attrs = set(IMPORTANT_ATTRS)

        # If you want to handle the root as well, use 'include_self=True'
        # so you don't miss attributes on the top-level element.
        # Manually include the root, then all its descendants
        for el in chain((root,), root.iterdescendants()):
            # We only remove attributes on HtmlElement nodes, skip comments or text nodes
            if not isinstance(el, lhtml.HtmlElement):
                continue

            old_attribs = dict(el.attrib)
            new_attribs = {}

            for attr_name, attr_val in old_attribs.items():
                # If it's an important attribute, keep it
                if attr_name in important_attrs:
                    new_attribs[attr_name] = attr_val
                # Or if keep_data_attributes is True and it's a 'data-*' attribute
                elif keep_data_attributes and attr_name.startswith("data-"):
                    new_attribs[attr_name] = attr_val

            # Clear old attributes and set the filtered set
            el.attrib.clear()
            el.attrib.update(new_attribs)

        return root