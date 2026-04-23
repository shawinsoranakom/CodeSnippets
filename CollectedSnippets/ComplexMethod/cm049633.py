def _compute_placeholder(self, html_string):
        """
        Transforms an HTML string by converting specific HTML tags into a custom
        pseudo-markdown format using context-stored state.
        :param html_string: The input HTML string to be transformed.
        :type html_string: str
        :return: (updated_processor, transformed_string) - The updated processor instance
                and the transformed string with HTML tags replaced by pseudo-markdown.
        :rtype: tuple
        """
        if not html_string or not html_string.strip():
            return self, html_string

        tree = etree.fromstring(f'<div>{html_string}</div>')

        # Identifying one or more wrapping tags that enclose the entire HTML
        # content e.g., <strong><em>text ...</em></strong>. Store them to
        # reapply them after processing with AI.
        wrapping_html = []
        for element in tree.iter():
            wrapping_html.append({"tag": element.tag, "attr": element.attrib})
            if len(element) != 1 \
                    or (element.text and element.text.strip()) \
                    or (element[-1].tail and element[-1].tail.strip()):
                break
        # Remove the wrapping element used for parsing into a tree
        wrapping_html = wrapping_html[1:]

        # Loop through all nodes, ignoring wrapping ones, to mark them with
        # a pseudo-markdown identifier if they are leaf nodes.
        nb_tags_to_skip = len(wrapping_html) + 1
        hash_updates = {}

        for cursor, element in enumerate(tree.iter()):
            if cursor < nb_tags_to_skip or len(element) > 0:
                continue

            # Generate a unique hash based on the element's text, tag
            # and attributes.
            attrib_string = ','.join(f'{key}={value}' for key, value in sorted(element.attrib.items()))
            combined_string = f'{element.text or ""}-{element.tag}-{attrib_string}'
            unique_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, combined_string)
            hash_value = unique_uuid.hex[:12]

            hash_updates[hash_value] = {"tag": element.tag, "attr": element.attrib}
            element.text = f'#[{element.text or "0"}]({hash_value})'

        # Start with current processor
        updated_processor = self

        # Update context with new hashes
        if hash_updates:
            updated_processor = updated_processor._update_processing_cache('html_hashes_to_tags_and_attributes', hash_updates)

        res = tree.xpath('string()')

        # If there is at least one wrapping tag, save the way it needs to
        # be re-applied.
        if wrapping_html:
            tags = [
                (
                    f'<{tag}{" " if attrs else ""}{attrs}>',
                    f'</{tag}>',
                )
                for el in wrapping_html
                for tag, attrs in [(el["tag"], " ".join([f'{k}="{v}"' for k, v in el["attr"].items()]))]
            ]
            opening_tags, closing_tags = zip(*tags)
            wrapping_pattern = f'{"".join(opening_tags)}$0{"".join(closing_tags[::-1])}'

            # Update context with wrapping tags
            updated_processor = updated_processor._update_processing_cache('html_string_to_wrapping_tags', {html_string: wrapping_pattern})

        # Note that `get_text_content` here is still needed despite the use
        # of `string()` in the XPath expression above. Indeed, it allows to
        # strip newlines and double-spaces, which would confuse IAP (without
        # this, it does not perform any replacement for some reason).
        result = xml_translate.get_text_content(res.strip())
        return updated_processor, result