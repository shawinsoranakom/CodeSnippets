def _merge_two_xml(
            cls,
            primary_xml: etree._Element,
            secondary_xml: etree._Element,
            overwrite_on_conflict=True,
            add_on_absent=True,
    ):
        """
        This method takes two _Element objects, and merge the content of the second _Element to the first one recursively.
        Here, we go through every text, and attribute of the secondary_xml and its children; and apply the following operation:

        - Search for a matching child element / attribute on the `primary_xml`
        - If a match is found, overwrite the matching `primary_xml` attribute/child/text if `overwrite_on_conflict` is True
        - If a match is not found, add on `primary_xml` if `add_on_absent` is True

        Warning: The `tag` of the two `_Element` object must be the same.

        For example:
        Before calling this method,
        primary_xml
        <a attr_1="old_attr_1">
            <b>old b text</b>
        </a>

        secondary_xml
        <a attr_1="new_attr_1" attr_2="new_attr_2>
            <b attr_b="new_attr_b">new text</b>
            <c>new element</c>
        </a>

        [#1] Resulting primary_xml post call with default optional parameters (overwrite_on_conflict True, add_on_absent True)
        <a attr_1="new_attr_1" attr_2="new_attr_2>
            <b attr_b="new_attr_b">new text</b>
            <c>new element</c>
        </a>

        [#2] Resulting primary_xml post call with (overwrite_on_conflict True, add_on_absent False)
        <a attr_1="new_attr_1">
            <b>new text</b>
        </a>

        [#3] Resulting primary_xml post call with (overwrite_on_conflict False, add_on_absent True)
        <a attr_1="old_attr_1" attr_2="new_attr_2>
            <b attr_b="new_attr_b">old b text</b>
            <c>new element</c>
        </a>

        [#4] Resulting primary_xml post call with (overwrite_on_conflict False, add_on_absent False)
        No change will be made with these configuration.

        :param primary_xml: The primary _Element object to be written on to.
        :param secondary_xml: The second _Element object in which content is used as reference.
        :param overwrite_on_conflict: If True and matching attribute/child element is found, the original content is overwritten.
        :param add_on_absent: If True and matching attribute/child element is not found, it will be added on the primary_xml.
        :return:
        """
        if primary_xml.tag != secondary_xml.tag:
            return

        for new_attrib_key, new_attrib_val in secondary_xml.items():
            if (new_attrib_key not in primary_xml.attrib and add_on_absent) or (new_attrib_key in primary_xml.attrib and overwrite_on_conflict):
                primary_xml.attrib[new_attrib_key] = new_attrib_val

        if secondary_xml.text and ((not primary_xml.text and overwrite_on_conflict) or (primary_xml.text and overwrite_on_conflict)):
            primary_xml.text = secondary_xml.text

        for new_child in secondary_xml.getchildren():
            found_match = False
            for current_child in primary_xml.getchildren():
                if current_child.tag == new_child.tag:
                    cls._merge_two_xml(
                        current_child,
                        new_child,
                        overwrite_on_conflict=overwrite_on_conflict,
                        add_on_absent=add_on_absent,
                    )
                    found_match = True

            if not found_match and add_on_absent:
                primary_xml.append(new_child)