def _validate_tag_groupby(self, node, name_manager, node_info):
        # groupby nodes should be considered as nested view because they may
        # contain fields on the comodel
        name = node.get('name')
        if not name:
            return
        field = name_manager.model._fields.get(name)
        if field:
            if node_info['validate']:
                if field.type != 'many2one':
                    msg = _(
                        "Field '%(name)s' found in 'groupby' node can only be of type many2one, found %(type)s",
                        name=field.name, type=field.type,
                    )
                    self._raise_view_error(msg, node)
                domain = node_info['editable'] and field._description_domain(self.env)
                if isinstance(domain, str):
                    desc = f"domain of python field '{name}'"
                    self._validate_domain_identifiers(node, name_manager, domain, desc, field.comodel_name, node_info)

            # move all children nodes into a new node <groupby>
            groupby_node = E.groupby(*node)
            # validate the node as a nested view
            self._validate_view(
                groupby_node, field.comodel_name, view_type="groupby", editable=False,
                node_info=node_info,
            )
            name_manager.has_field(node, name, node_info)

        elif node_info['validate']:
            msg = _(
                "Field '%(field)s' found in 'groupby' node does not exist in model %(model)s",
                field=name, model=name_manager.model._name,
            )
            self._raise_view_error(msg, node)