def xml(self):
        """
        Create a list of blocks. A block can have one of the two types "templates" or "extensions".
        A template with no parent or template with t-inherit-mode="primary" goes in a block of type "templates".
        A template with t-inherit-mode="extension" goes in a block of type "extensions".

        Used parsed attributes:
        * `t-name`: template name
        * `t-inherit`: inherited template name.
        * 't-inherit-mode':  'primary' or 'extension'.

        :return a list of blocks
        """
        parser = etree.XMLParser(ns_clean=True, recover=True, remove_comments=True)

        blocks = []
        block = None
        for asset in self.templates:
            # Load content.
            try:
                content = asset.content.strip()
                template = content if content.startswith('<odoo>') else f'<templates>{asset.content}</templates>'
                io_content = io.BytesIO(template.encode('utf-8'))
                content_templates_tree = etree.parse(io_content, parser=parser).getroot()
            except etree.ParseError as e:
                return asset.generate_error(f'Could not parse file: {e.msg}')
            # Process every templates.
            for template_tree in list(content_templates_tree):
                template_name = template_tree.get("t-name")
                inherit_from = template_tree.get("t-inherit")
                inherit_mode = None
                if inherit_from:
                    inherit_mode = template_tree.get('t-inherit-mode', 'primary')
                    if inherit_mode not in ['primary', 'extension']:
                        addon = asset.url.split('/')[1]
                        return asset.generate_error(self.env._(
                            'Invalid inherit mode. Module "%(module)s" and template name "%(template_name)s"',
                            module=addon,
                            template_name=template_name,
                        ))
                if inherit_mode == "extension":
                    if block is None or block["type"] != "extensions":
                        block = {"type": "extensions", "extensions": OrderedDict()}
                        blocks.append(block)
                    block["extensions"].setdefault(inherit_from, [])
                    block["extensions"][inherit_from].append((template_tree, asset.url))
                elif template_name:
                    if block is None or block["type"] != "templates":
                        block = {"type": "templates", "templates": []}
                        blocks.append(block)
                    block["templates"].append((template_tree, asset.url, inherit_from))
                else:
                    return asset.generate_error(self.env._("Template name is missing."))
        return blocks