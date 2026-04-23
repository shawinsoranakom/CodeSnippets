def _validate_view(self, node, model_name, view_type=None, editable=True, node_info=None):
        """ Validate the given architecture node, and return its corresponding
        NameManager.

        :param self: the view being validated
        :param node: the combined architecture as an etree
        :param model_name: the reference model name for the given architecture
        :param view_type:
        :param editable: whether the view is considered editable
        :param node_info:
        :return: the combined architecture's NameManager
        """
        self.ensure_one()

        view_type = view_type or self.type
        if node.tag != view_type:
            self._raise_view_error(_(
                'The root node of a %(view_type)s view should be a <%(view_type)s>, not a <%(tag)s>',
                view_type=view_type, tag=node.tag,
            ), node)

        if model_name not in self.env:
            self._raise_view_error(_('Model not found: %(model)s', model=model_name), node)

        group_definitions = self.env['res.groups']._get_group_definitions()

        # model_groups/view_groups: access groups for the model/view
        validate = node_info['validate'] if node_info else False
        model_groups = node_info['model_groups'] if node_info else group_definitions.universe
        view_groups = node_info['view_groups'] if node_info else group_definitions.universe
        parent_name_manager = node_info['name_manager'] if node_info else None

        # combine model access groups with this model's access groups
        model_groups &= self.env['ir.model.access']._get_access_groups(model_name)

        # fields_get() optimization: validation does not require translations
        model = self.env[model_name].with_context(lang=None)
        name_manager = NameManager(model, parent=parent_name_manager, model_groups=model_groups)

        view_type = node.tag
        # use a stack to recursively traverse the tree
        stack = [(node, view_groups, editable, validate)]
        while stack:
            node, view_groups, editable, validate = stack.pop()

            # compute default
            tag = node.tag
            validate = validate or node.get('__validate__')
            node_info = {
                'editable': editable and self._editable_node(node, name_manager),
                'validate': validate,
                'view_type': view_type,
                'model_groups': model_groups,
                'view_groups': view_groups,
                'name_manager': name_manager,
            }

            if groups := node.get('groups'):
                for group_name in groups.replace('!', '').split(','):
                    name_manager.must_exist_group(group_name, node)
                node_info['view_groups'] &= group_definitions.parse(groups, raise_if_not_found=False)

            # tag-specific validation
            validator = getattr(self, f"_validate_tag_{tag}", None)
            if validator is not None:
                validator(node, name_manager, node_info)

            if validate:
                self._validate_attributes(node, name_manager, node_info)

            for child in reversed(node):
                stack.append((child, node_info['view_groups'], node_info['editable'], validate))

        name_manager.check(self)

        return name_manager