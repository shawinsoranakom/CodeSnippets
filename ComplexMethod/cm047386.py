def _fetch_template_views(self, ids_or_xmlids: Sequence[int | str]) -> dict[int | str, models.BaseModel | Exception]:
        """ Return the view corresponding to ``template``, which may be a
            view ID or an XML ID. Note that this method may be overridden for other
            kinds of template values.
        """
        IrUiView = self.env['ir.ui.view'].sudo().with_context(load_all_views=True, raise_if_not_found=True)

        ids, xmlids = partition(lambda v: isinstance(v, int), ids_or_xmlids)

        # search view in ir.ui.view
        view_by_id = {}
        field_names = [f.name for f in IrUiView._fields.values() if f.prefetch is True]
        if xmlids:
            domain = Domain('id', 'in', ids) | Domain(self._get_template_domain(xmlids))
            views = IrUiView.search_fetch(domain, field_names, order=self._get_template_order())
        else:
            views = IrUiView.browse(ids)

        for view in views:
            try:
                if view.key in view_by_id:
                    # keeps views according to their priority order
                    continue
            except MissingError:
                continue
            view_by_id[view.id] = view
            if view.key:
                view_by_id[view.key] = view

        # search missing view from xmlid in ir.model.data
        missing_xmlid_views = [xmlid for xmlid in xmlids if '.' in xmlid and xmlid not in view_by_id]
        if missing_xmlid_views:
            domain = Domain.OR(
                Domain('model', '=', 'ir.ui.view') & Domain('module', '=', res[0]) & Domain('name', '=', res[1])
                for xmlid in missing_xmlid_views
                if (res := xmlid.split('.', 1))
            )

            for model_data in self.env['ir.model.data'].sudo().search(domain):
                view = IrUiView.browse(model_data.res_id)
                if view.exists():
                    view_by_id[view.id] = view
                    xmlid = f"{model_data.module}.{model_data.name}"
                    view_by_id[xmlid] = view
                    if view.key:
                        view_by_id[view.key] = view

        for key, view in view_by_id.items():
            # push information in cache
            self._get_cached_template_info(key, _view=view)

        # create data and errors
        for view_id in ids:
            if view_id not in view_by_id:
                # push information in cache
                self._get_cached_template_info(view_id, _view=False)
                view_by_id[view_id] = MissingError(self.env._("Template does not exist or has been deleted: %s", view_id))
        for xmlid in xmlids:
            if xmlid not in view_by_id:
                # push information in cache
                self._get_cached_template_info(xmlid, _view=False)
                view_by_id[xmlid] = MissingError(self.env._("Template not found: '%s'", xmlid))
        return view_by_id