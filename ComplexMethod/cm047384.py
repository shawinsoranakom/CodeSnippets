def _get_combined_archs(self):
        """ Return the arch of ``self`` (as an etree) combined with its inherited views. """
        parented = []
        roots = self.env['ir.ui.view']
        for root in self:
            parented.append(view_ids := [])
            while True:
                view_ids.append(root.id)
                if not root.inherit_id:
                    roots += root
                    break
                root = root.inherit_id
        views = self.env['ir.ui.view'].browse(unique(view_id for view_ids in parented for view_id in view_ids))

        # Add inherited views to the list of loading forced views
        # Otherwise, inherited views could not find elements created in
        # their direct parents if that parent is defined in the same module
        # introduce check_view_ids in context
        if 'check_view_ids' not in views.env.context:
            views = views.with_context(check_view_ids=[])
        views.env.context['check_view_ids'].extend(views.ids)

        # Map each node to its children nodes. Note that all children nodes are
        # part of a single prefetch set, which is all views to combine.
        all_tree_views = views._get_inheriting_views()

        # During an upgrade, we can only use the views that have been
        # fully upgraded already.
        if self.pool._init and not self.env.context.get('load_all_views'):
            all_tree_views = all_tree_views._filter_loaded_views(set(views.env.context['check_view_ids']))

        # get the global children views then get hierarchy for each views
        children_views = collections.defaultdict(list)
        for view in all_tree_views:
            children_views[view.inherit_id].append(view)

        def get_hierarchy(root, parented_ids, _hierarchy=None):
            if _hierarchy is None:
                _hierarchy = collections.defaultdict(list)
            _hierarchy[root.inherit_id].append(root)
            for child in children_views[root]:
                if child.id in parented_ids or child.mode != 'primary':
                    get_hierarchy(child, parented_ids, _hierarchy)
            return _hierarchy

        roots = roots.with_prefetch(all_tree_views._prefetch_ids)

        return [
            root._combine(get_hierarchy(root, parented_ids))
            for root, parented_ids in zip(roots, parented)
        ]