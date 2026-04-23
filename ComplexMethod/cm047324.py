def generate_xml_bundle(self):
        content = []
        blocks = []
        try:
            blocks = self.xml()
        except XMLAssetError as e:
            content.append(f'throw new Error({json.dumps(str(e))});')

        def get_template(element):
            element.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            string = etree.tostring(element, encoding='unicode')
            return string.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

        names = OrderedSet()
        primary_parents = OrderedSet()
        extension_parents = OrderedSet()
        for block in blocks:
            if block["type"] == "templates":
                for (element, url, inherit_from) in block["templates"]:
                    if inherit_from:
                        primary_parents.add(inherit_from)
                    name = element.get("t-name")
                    names.add(name)
                    template = get_template(element)
                    content.append(f'registerTemplate("{name}", `{url}`, `{template}`);')
            else:
                for inherit_from, elements in block["extensions"].items():
                    extension_parents.add(inherit_from)
                    for (element, url) in elements:
                        template = get_template(element)
                        content.append(f'registerTemplateExtension("{inherit_from}", `{url}`, `{template}`);')

        missing_names_for_primary = primary_parents - names
        if missing_names_for_primary:
            content.append(f'checkPrimaryTemplateParents({json.dumps(list(missing_names_for_primary))});')
        missing_names_for_extension = extension_parents - names
        if missing_names_for_extension:
            content.append(f'console.error("Missing (extension) parent templates: {", ".join(missing_names_for_extension)}");')

        return '\n'.join(content)