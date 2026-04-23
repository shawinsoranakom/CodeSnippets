def _postprocess_view(self, node, model_name, editable=True, node_info=None, **options):
        """ Process the given architecture, modifying it in-place to add and
        remove stuff.

        :param self: the optional view to postprocess
        :param node: the combined architecture as an etree
        :param model_name: the view's reference model name
        :param editable: whether the view is considered editable
        :return: the processed architecture's NameManager
        """
        root = node

        if model_name not in self.env:
            self._raise_view_error(_('Model not found: %(model)s', model=model_name), root)
        model = self.env[model_name]

        group_definitions = self.env['res.groups']._get_group_definitions()

        # model_groups/view_groups: access groups for the model/view
        model_groups = node_info['model_groups'] if node_info else group_definitions.universe
        view_groups = node_info['view_groups'] if node_info else group_definitions.universe
        parent_name_manager = node_info['name_manager'] if node_info else None

        # combine model access groups with this model's access groups
        model_groups &= self.env['ir.model.access']._get_access_groups(model_name)

        name_manager = NameManager(model, parent=parent_name_manager, model_groups=model_groups)

        root_info = {
            'view_type': root.tag,
            'view_editable': editable and self._editable_node(root, name_manager),
            'mobile': options.get('mobile'),
            'model_groups': model_groups,
            'view_groups': view_groups,
            'name_manager': name_manager,
        }

        is_compute_warning_info = options.get('is_compute_warning_info')

        self._postprocess_debug_to_cache(root)

        # use a stack to recursively traverse the tree
        stack = [(root, view_groups, editable)]
        while stack:
            node, view_groups, editable = stack.pop()

            # compute default
            tag = node.tag
            had_parent = node.getparent() is not None
            node_info = dict(root_info, view_groups=view_groups, editable=editable and self._editable_node(node, name_manager))

            node_groups = node.get('groups')
            if node_groups:
                node_info['view_groups'] &= group_definitions.parse(node_groups, raise_if_not_found=False)

            # tag-specific postprocessing
            postprocessor = getattr(self, f"_postprocess_tag_{tag}", None)
            if postprocessor is not None:
                postprocessor(node, name_manager, node_info)
                if had_parent and node.getparent() is None:
                    # the node has been removed, stop processing here
                    continue

            # if present, iterate on node_info['children'] instead of node
            for child in reversed(node_info.get('children', node)):
                stack.append((child, node_info['view_groups'], node_info['editable']))

            if node_groups or root_info['model_groups'] != node_info['model_groups']:
                groups = node_info['model_groups'] & node_info['view_groups']
                node.set('__groups_key__', groups.key)

            self._postprocess_attributes(node, name_manager, node_info)

            if node_groups and is_compute_warning_info:
                # reset the groups attributes to display in log
                node.attrib['groups'] = node_groups

        missing_fields = self._add_missing_fields(root, name_manager)

        if is_compute_warning_info:
            for name, (missing_groups, reasons) in missing_fields.items():
                error_message = name_manager._error_message_group_inconsistency(name, missing_groups, reasons)[0]
                if error_message:
                    if self.warning_info:
                        self.warning_info += Markup('<br/>\n<br/>\n')
                    self.warning_info += error_message.replace('\n', Markup('<br/>\n'))

        name_manager.update_available_fields()

        root.set('model_access_rights', model._name)

        if self._onchange_able_view(root):
            self._postprocess_on_change(root, model)

        return name_manager