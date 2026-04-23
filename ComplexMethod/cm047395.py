def _validate_tag_filter(self, node, name_manager, node_info):
        if not node_info['validate']:
            return
        domain = node.get('domain')
        if domain:
            name = node.get('name')
            desc = f'domain of <filter name="{name}">' if name else 'domain of <filter>'
            self._validate_domain_identifiers(node, name_manager, domain, desc, name_manager.model._name, node_info)
        if node.get("date") and (default_periods := node.get("default_period")):
            custom_options = {f'custom_{child.attrib["name"]}' for child in node.getchildren()}
            for default_period in default_periods.split(","):
                if not re.fullmatch(r"(year|month)((-|\+)[1-9]\d*)?", default_period)\
                    and default_period not in custom_options | {"first_quarter", "second_quarter", "third_quarter", "fourth_quarter"}:
                    msg = _(
                        "Invalid default period %(default_period)s for date filter",
                        default_period=default_period,
                    )
                    self._raise_view_error(msg, node)