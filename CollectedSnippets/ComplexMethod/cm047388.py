def _postprocess_access_rights(self, tree):
        """
        Apply group restrictions: elements with a 'groups' attribute should
        be removed from the view to people who are not members.

        Compute and set on node access rights based on view type. Specific
        views can add additional specific rights like creating columns for
        many2one-based grouping views.
        """
        group_definitions = self.env['res.groups']._get_group_definitions()

        user_group_ids = self.env.user._get_group_ids()

        # check the read/visibility access
        @functools.cache
        def has_access(groups_key):
            groups = group_definitions.from_key(groups_key)
            return groups.matches(user_group_ids)

        # check the read/visibility access
        for node in tree.xpath('//*[@__groups_key__]'):
            if not has_access(node.attrib.pop('__groups_key__')):
                tail = node.tail
                parent = node.getparent()
                previous = node.getprevious()
                parent.remove(node)
                if tail:
                    if previous is not None:
                        previous.tail = (previous.tail or '') + tail
                    elif parent is not None:
                        parent.text = (parent.text or '') + tail
            elif node.tag == 't' and not node.attrib:
                # Move content of <t groups=""> blocks
                # and remove the <t> node.
                # This is to keep the structure
                # <group>
                #   <field name="foo"/>
                #   <field name="bar"/>
                # <group>
                # so the web client adds the label as expected.
                # This is also to avoid having <t> nodes in list views
                # e.g.
                # <list>
                #   <field name="foo"/>
                #   <t groups="foo">
                #     <field name="bar" groups="bar"/>
                #   </t>
                # </list>
                for child in reversed(node):
                    node.addnext(child)
                node.getparent().remove(node)

        # check the create and write access
        for node in tree.xpath('//*[@model_access_rights]'):
            model = self.env[node.attrib.pop('model_access_rights')]
            if node.tag == 'field':
                can_create = model.has_access('create')
                can_write = model.has_access('write')
                node.set('can_create', str(bool(can_create)))
                node.set('can_write', str(bool(can_write)))
            else:
                for action, operation in (('create', 'create'), ('delete', 'unlink'), ('edit', 'write')):
                    if not node.get(action) and not model.has_access(operation):
                        node.set(action, 'False')
                if node.tag == 'kanban':
                    group_by_name = node.get('default_group_by')
                    group_by_field = model._fields.get(group_by_name)
                    if group_by_field and group_by_field.type == 'many2one':
                        group_by_model = model.env[group_by_field.comodel_name]
                        for action, operation in (('group_create', 'create'), ('group_delete', 'unlink'), ('group_edit', 'write')):
                            if not node.get(action) and not group_by_model.has_access(operation):
                                node.set(action, 'False')

        return tree