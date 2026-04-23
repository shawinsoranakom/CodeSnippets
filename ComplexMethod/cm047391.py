def _get_x2many_missing_view_archs(self, field, field_node, node_info):
        """
        For x2many fields that require to have some multi-record arch (kanban or list) to display the records
        be available, this function fetches all arch that are needed and return them.
        The caller function is responsible to do what it needs with them.
        """
        current_view_types = [el.tag for el in field_node.xpath("./*[descendant::field]")]
        missing_view_types = []
        if not any(view_type in current_view_types for view_type in field_node.get('mode', 'kanban,list').split(',')):
            missing_view_types.append(
                field_node.get('mode', 'kanban' if node_info.get('mobile') else 'list').split(',')[0]
            )

        if not missing_view_types:
            return []

        comodel = self.env[field.comodel_name].sudo(False)
        refs = self._get_view_refs(field_node)
        # Do not propagate <view_type>_view_ref of parent call to `_get_view`
        comodel = comodel.with_context(**{
            f'{view_type}_view_ref': refs.get(f'{view_type}_view_ref')
            for view_type in missing_view_types
        })

        return [comodel._get_view(view_type=view_type) for view_type in missing_view_types]