def _extract_thumbnails(self, flix_xml):

        def get_child(elem, names):
            for name in names:
                child = elem.find(name)
                if child is not None:
                    return child

        timeline = get_child(flix_xml, ['timeline', 'rolloverBarImage'])
        if timeline is None:
            return

        pattern_el = get_child(timeline, ['imagePattern', 'pattern'])
        if pattern_el is None or not pattern_el.text:
            return

        first_el = get_child(timeline, ['imageFirst', 'first'])
        last_el = get_child(timeline, ['imageLast', 'last'])
        if first_el is None or last_el is None:
            return

        first_text = first_el.text
        last_text = last_el.text
        if not first_text.isdigit() or not last_text.isdigit():
            return

        first = int(first_text)
        last = int(last_text)
        if first > last:
            return

        width = int_or_none(xpath_text(timeline, './imageWidth', 'thumbnail width'))
        height = int_or_none(xpath_text(timeline, './imageHeight', 'thumbnail height'))

        return [{
            'url': self._proto_relative_url(pattern_el.text.replace('#', str(i)), 'http:'),
            'width': width,
            'height': height,
        } for i in range(first, last + 1)]