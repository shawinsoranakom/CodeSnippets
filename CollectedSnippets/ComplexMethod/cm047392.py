def _postprocess_tag_field(self, node, name_manager, node_info):
        name = node.get('name')
        if not name:
            return

        attrs = {'id': node.get('id'), 'select': node.get('select')}
        field = name_manager.model._fields.get(name)

        if field:
            if field.groups:
                group_definitions = self.env['res.groups']._get_group_definitions()
                node_info['model_groups'] &= group_definitions.parse(field.groups, raise_if_not_found=False)
            if (
                node_info.get('view_type') == 'form'
                and field.type in ('one2many', 'many2many')
                and not node.get('widget')
                and node.get('invisible') not in ('1', 'True')
                and not name_manager.parent
            ):
                # Embed kanban/list/form views for visible x2many fields in form views
                # if no widget or the widget requires it.
                # So the web client doesn't have to call `get_views` for x2many fields not embedding their view
                # in the main form view.
                for arch, _view in self._get_x2many_missing_view_archs(field, node, node_info):
                    node.append(arch)

            if field.relational:
                domain = (
                    node.get('domain')
                    or node_info['editable'] and field._description_domain(self.env)
                )
                if isinstance(domain, str):
                    vnames = get_expression_field_names(domain)
                    name_manager.must_have_fields(node, vnames, node_info, ('domain', domain))
            if field.type == 'properties':
                name_manager.must_have_fields(node, [field.definition_record], node_info, ('fieldname', field.name))
            context = node.get('context')
            if context:
                vnames = get_expression_field_names(context)
                name_manager.must_have_fields(node, vnames, node_info, ('context', context))
            if field.type == "binary" and (field_filename := node.get("filename")):
                name_manager.must_have_fields(node, [field_filename], node_info, ("filename", field_filename))

            for child in node:
                if child.tag in ('form', 'list', 'graph', 'kanban', 'calendar'):
                    node_info['children'] = []
                    self._postprocess_view(child, field.comodel_name, editable=node_info['editable'], node_info=node_info)

            if node_info['editable'] and field.type in ('many2one', 'many2many'):
                node.set('model_access_rights', field.comodel_name)

        name_manager.has_field(node, name, node_info, attrs)