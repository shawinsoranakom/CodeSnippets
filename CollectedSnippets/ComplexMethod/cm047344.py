def _prepare_html(self, html, report_model=False):
        '''Divide and recreate the header/footer html by merging all found in html.
        The bodies are extracted and added to a list. Then, extract the specific_paperformat_args.
        The idea is to put all headers/footers together. Then, we will use a javascript trick
        (see minimal_layout template) to set the right header/footer during the processing of wkhtmltopdf.
        This allows the computation of multiple reports in a single call to wkhtmltopdf.
        '''

        # Return empty dictionary if 'web.minimal_layout' not found.
        layout = self._get_layout()
        if not layout:
            return {}
        base_url = self._get_report_url(layout=layout)

        root = lxml.html.fromstring(html, parser=lxml.html.HTMLParser(encoding='utf-8'))
        match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

        header_node = etree.Element('div', id='minimal_layout_report_headers')
        footer_node = etree.Element('div', id='minimal_layout_report_footers')
        bodies = []
        res_ids = []

        body_parent = root.xpath('//main')[0]
        # Retrieve headers
        for node in root.xpath(match_klass.format('header')):
            body_parent = node.getparent()
            node.getparent().remove(node)
            header_node.append(node)

        # Retrieve footers
        for node in root.xpath(match_klass.format('footer')):
            body_parent = node.getparent()
            node.getparent().remove(node)
            footer_node.append(node)

        # Retrieve bodies
        for node in root.xpath(match_klass.format('article')):
            # set context language to body language
            IrQweb = self.env['ir.qweb']
            if node.get('data-oe-lang'):
                IrQweb = IrQweb.with_context(lang=node.get('data-oe-lang'))
            body = IrQweb._render(layout.id, {
                    'subst': False,
                    'body': Markup(lxml.html.tostring(node, encoding='unicode')),
                    'base_url': base_url,
                    'report_xml_id': self.xml_id,
                    'debug': self.env.context.get("debug"),
                }, raise_if_not_found=False)
            bodies.append(body)
            if node.get('data-oe-model') == report_model:
                res_ids.append(int(node.get('data-oe-id', 0)))
            else:
                res_ids.append(None)

        if not bodies:
            body = ''.join(lxml.html.tostring(c, encoding='unicode') for c in body_parent.getchildren())
            bodies.append(body)

        # Get paperformat arguments set in the root html tag. They are prioritized over
        # paperformat-record arguments.
        specific_paperformat_args = {}
        for attribute in root.items():
            if attribute[0].startswith('data-report-'):
                specific_paperformat_args[attribute[0]] = attribute[1]

        header = self.env['ir.qweb']._render(layout.id, {
            'subst': True,
            'body': Markup(lxml.html.tostring(header_node, encoding='unicode')),
            'base_url': base_url,
            'report_xml_id': self.xml_id,
            'debug': self.env.context.get("debug"),
        })
        footer = self.env['ir.qweb']._render(layout.id, {
            'subst': True,
            'body': Markup(lxml.html.tostring(footer_node, encoding='unicode')),
            'base_url': base_url,
            'report_xml_id': self.xml_id,
            'debug': self.env.context.get("debug"),
        })

        return bodies, res_ids, header, footer, specific_paperformat_args