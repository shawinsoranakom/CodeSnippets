def _check_xml(self):
        # Sanity checks: the view should not break anything upon rendering!
        # Any exception raised below will cause a transaction rollback.
        partial_validation = self.env.context.get('ir_ui_view_partial_validation')
        views = self.with_context(validate_view_ids=(self._ids if partial_validation else True))

        for view in views:
            if partial_validation and not view.arch:
                continue
            try:
                # verify the view is valid xml and that the inheritance resolves
                if view.inherit_id:
                    view_arch = etree.fromstring(view.arch or '<data/>')
                    view._valid_inheritance(view_arch)

                combined_arch = view._get_combined_arch()

                # check primary view that extends this current view
                # keep a way to skip this check to avoid marking too many views as failed during an upgrade
                if not self.env.context.get('_skip_primary_extensions_check') and (view.inherit_id or view.inherit_children_ids):
                    root = view
                    while root.inherit_id and root.mode != 'primary':
                        root = root.inherit_id
                    sibling_primary_views = self.env['ir.ui.view']
                    stack = [root]
                    while stack:
                        root = stack.pop()
                        for child in root.inherit_children_ids:
                            if child.mode == 'primary':
                                sibling_primary_views += child
                            else:
                                stack.append(child)

                    # During an upgrade, we can only use the views that have been
                    # fully upgraded already.
                    if self.pool._init and sibling_primary_views and self.pool._init_modules:
                        query = sibling_primary_views._get_filter_xmlid_query()
                        sql = SQL(query, res_ids=tuple(sibling_primary_views.ids), modules=tuple(self.pool._init_modules))
                        loaded_view_ids = {id_ for id_, in self.env.execute_query(sql)}
                        loaded_view_ids.update({
                            id
                            for id, xid in (sibling_primary_views - views.browse(loaded_view_ids)).get_external_id().items()
                            if xid in self.pool.loaded_xmlids
                        })
                        sibling_primary_views = sibling_primary_views.browse(loaded_view_ids)

                    # Check if we know how to apply inheritances
                    sibling_primary_views._get_combined_archs()

                if view.type == 'qweb':
                    continue
            except (etree.ParseError, ValueError) as e:
                err = ValidationError(_(
                    "Error while parsing or validating view:\n\n%(error)s",
                    error=e,
                    view=view.key or view.id,
                )).with_traceback(e.__traceback__)
                err.context = getattr(e, 'context', None)
                raise err from None

            try:
                # verify that all fields used are valid, etc.
                view._validate_view(combined_arch, view.model)
                combined_archs = [combined_arch]

                if combined_arch.xpath('//*[@attrs]') or combined_arch.xpath('//*[@states]'):
                    view_name = f'{view.name} ({view.xml_id})' if view.xml_id else view.name
                    err = ValidationError(_('Since 17.0, the "attrs" and "states" attributes are no longer used.\nView: %(name)s in %(file)s',
                        name=view_name, file=view.arch_fs
                    ))
                    err.context = {'name': 'invalid view'}
                    raise err

                if combined_archs[0].tag == 'data':
                    # A <data> element is a wrapper for multiple root nodes
                    combined_archs = combined_archs[0]
                for view_arch in combined_archs:
                    for node in view_arch.xpath('//*[@__validate__]'):
                        del node.attrib['__validate__']
                    check = valid_view(view_arch, env=self.env, model=view.model)
                    if not check:
                        view_name = f'{view.name} ({view.xml_id})' if view.xml_id else view.name
                        raise ValidationError(_(
                            'Invalid view %(name)s definition in %(file)s',
                            name=view_name, file=view.arch_fs
                        ))
            except ValueError as e:
                if hasattr(e, 'context'):
                    lines = etree.tostring(combined_arch, encoding='unicode').splitlines(keepends=True)
                    fivelines = "".join(lines[max(0, e.context["line"]-3):e.context["line"]+2])
                    err = ValidationError(_(
                        "Error while validating view near:\n\n%(fivelines)s\n%(error)s",
                        fivelines=fivelines, error=e,
                    ))
                    err.context = e.context
                    raise err.with_traceback(e.__traceback__) from None
                elif e.__context__:
                    err = ValidationError(_(
                        "Error while validating view (%(view)s):\n\n%(error)s", view=view.key or view.id, error=e.__context__,
                    ))
                    err.context = {'name': 'invalid view'}
                    raise err.with_traceback(e.__context__.__traceback__) from None
                else:
                    raise ValidationError(_(
                        "Error while validating view (%(view)s):\n\n%(error)s", view=view.key or view.id, error=e,
                    ))

        return True