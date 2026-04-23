def _views_get(self, view_id, get_children=True, bundles=False, root=True, visited=None):
        """ For a given view ``view_id``, should return:
                * the view itself (starting from its top most parent)
                * all views inheriting from it, enabled or not
                  - but not the optional children of a non-enabled child
                * all views called from it (via t-call)

            :returns: recordset of ir.ui.view
        """
        try:
            if isinstance(view_id, models.BaseModel):
                view = view_id
            else:
                view = self._get_template_view(view_id)
        except MissingError:
            _logger.warning("Could not find view object with view_id '%s'", view_id)
            return self.env['ir.ui.view']

        if visited is None:
            visited = []
        original_hierarchy = self.env.context.get('__views_get_original_hierarchy', [])
        while root and view.inherit_id:
            original_hierarchy.append(view.id)
            view = view.inherit_id

        views_to_return = view

        if view.arch and view.arch.strip():
            node = etree.fromstring(view.arch)
            xpath = "//t[@t-call]"
            if bundles:
                xpath += "| //t[@t-call-assets]"
            for child in node.xpath(xpath):
                try:
                    called_view = self._get_template_view(child.get('t-call', child.get('t-call-assets')))
                except MissingError:
                    continue
                if called_view and called_view not in views_to_return and called_view.id not in visited:
                    views_to_return += self._views_get(called_view, get_children=get_children, bundles=bundles, visited=visited + views_to_return.ids)

        if not get_children:
            return views_to_return

        extensions = self._view_get_inherited_children(view)

        # Keep children in a deterministic order regardless of their applicability
        for extension in extensions.sorted(key=lambda v: v.id):
            # only return optional grandchildren if this child is enabled
            if extension.id not in visited:
                for ext_view in self._views_get(extension, get_children=extension.active, root=False, visited=visited + views_to_return.ids):
                    if ext_view not in views_to_return:
                        views_to_return += ext_view
        return views_to_return