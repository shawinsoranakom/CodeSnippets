def contains_description(node, depth=0):
            if depth > 2:
                _logger.warning('excessive depth in fa')
            if any(node.get(attr) for attr in valid_t_attrs):
                return True
            if has_title_or_aria_label(node):
                return True
            if node.tag in ('label', 'field'):
                return True
            if node.text:  # not sure, does it match *[text()]
                return True
            return any(contains_description(child, depth+1) for child in node)