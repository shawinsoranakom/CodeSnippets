def _get_template(self, template):
        """ Retrieve the given template, and return it as a tuple ``(etree,
        xml, ref)``, where ``element`` is an etree, ``document`` is the
        string document that contains ``element``, and ``ref`` if the uniq
        reference of the template (id, t-name or template).

        :param template: template identifier or etree
        """
        assert template not in (False, None, ""), "template is required"

        # template is an xml etree already
        if isinstance(template, etree._Element):
            element = template
            document = etree.tostring(template, encoding='unicode')

            # <templates>
            #   <template t-name=... /> <!-- return ONLY this element -->
            #   <template t-name=... />
            # </templates>
            for node in element.iter():
                ref = node.get('t-name')
                if ref:
                    return (node, document, _id_or_xmlid(ref))

            return (element, document, 'etree._Element')

        # template is xml as string
        if isinstance(template, str) and '<' in template:
            raise ValueError('Inline templates must be passed as `etree` documents')

        # template is (id or ref) to a database stored template
        id_or_xmlid = _id_or_xmlid(template)  # e.g. <t t-call="33"/> or <t t-call="web.layout"/>
        value = self._preload_trees([id_or_xmlid]).get(id_or_xmlid)
        if value.get('error'):
            raise value['error']

        # In dev mode `_generate_code_cached` is not cached and the tree can be processed several times
        value_tree = deepcopy(value['tree']) if 'xml' in tools.config['dev_mode'] else value['tree']
        # return etree, document and ref
        return (value_tree, value['template'], value['ref'])