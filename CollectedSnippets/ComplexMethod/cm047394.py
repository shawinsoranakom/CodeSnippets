def _validate_tag_field(self, node, name_manager, node_info):
        validate = node_info['validate']

        name = node.get('name')
        if not name:
            self._raise_view_error(_("Field tag must have a \"name\" attribute defined"), node)

        field = name_manager.model._fields.get(name)
        if field:
            if field.groups:
                group_definitions = self.env['res.groups']._get_group_definitions()
                node_info['model_groups'] &= group_definitions.parse(field.groups, raise_if_not_found=False)

            if validate and field.relational:
                domain = (
                    node.get('domain')
                    or node_info['editable'] and field._description_domain(self.env)
                )
                if isinstance(domain, str):
                    # dynamic domain: in [('foo', '=', bar)], field 'foo' must
                    # exist on the comodel and field 'bar' must be in the view
                    desc = (f'domain of <field name="{name}">' if node.get('domain')
                            else f"domain of python field {name!r}")
                    self._validate_domain_identifiers(node, name_manager, domain, desc, field.comodel_name, node_info)

            elif validate and node.get('domain'):
                msg = _(
                    'Domain on non-relational field "%(name)s" makes no sense (domain:%(domain)s)',
                    name=name, domain=node.get('domain'),
                )
                self._raise_view_error(msg, node)

            if field.type == 'properties' and node_info['view_type'] != 'search':
                name_manager.must_have_fields(node, {field._description_definition_record}, node_info, use=f"definition record of {field.name}")

            for child in node:
                if child.tag not in ('form', 'list', 'graph', 'kanban', 'calendar'):
                    continue
                node.remove(child)
                self._validate_view(
                    child, field.comodel_name, view_type=child.tag, editable=node_info['editable'],
                    node_info=node_info,
                )

        elif validate and name not in name_manager.field_info:
            msg = _(
                'Field "%(field_name)s" does not exist in model "%(model_name)s"',
                field_name=name, model_name=name_manager.model._name,
            )
            self._raise_view_error(msg, node)

        name_manager.has_field(node, name, node_info, {'id': node.get('id'), 'select': node.get('select')})