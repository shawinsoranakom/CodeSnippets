def _validate_fa_class_accessibility(self, node, description):
        valid_aria_attrs = {
            *att_names('title'), *att_names('aria-label'), *att_names('aria-labelledby'),
        }
        valid_t_attrs = {'t-value', 't-raw', 't-field', 't-esc', 't-out'}

        ## Following or preceding text
        if (node.tail or '').strip() or (node.getparent().text or '').strip():
            # text<i class="fa-..."/> or <i class="fa-..."/>text or
            return

        ## Following or preceding text in span
        def has_text(elem):
            if elem is None:
                return False
            if elem.tag == 'span' and elem.text:
                return True
            if elem.tag in ['field', 'label'] and elem.get('string'):
                return True
            if elem.tag == 't' and (elem.get('t-esc') or elem.get('t-raw')):
                return True
            return False

        if has_text(node.getnext()) or has_text(node.getprevious()):
            return

        def has_title_or_aria_label(node):
            return any(node.get(attr) for attr in valid_aria_attrs)

        ## Aria label can be on ancestors
        if any(map(has_title_or_aria_label, node.iterancestors())):
            return

        if node.get('string'):
            return

        ## And we ignore all elements with describing in children
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

        if contains_description(node):
            return

        msg = '%s must have title in its tag, parents, descendants or have text'
        self._log_view_warning(msg % description, node)