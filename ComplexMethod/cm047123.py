def _get_one2many_edition_view(self, field_info, node, level):
        """ Return a suitable view for editing records into a one2many field. """
        submodel = self._env[field_info['relation']]

        # by simplicity, ensure we always have tree and form views
        views = {
            view.tag: view for view in node.xpath('./*[descendant::field]')
        }
        for view_type in ['list', 'form']:
            if view_type in views:
                continue
            if field_info['invisible'] == 'True':
                # add an empty view
                views[view_type] = etree.Element(view_type)
                continue
            refs = self._env['ir.ui.view']._get_view_refs(node)
            subviews = submodel.with_context(**refs).get_views([(None, view_type)])
            subnode = etree.fromstring(subviews['views'][view_type]['arch'])
            views[view_type] = subnode
            node.append(subnode)
            for model_name, value in subviews['models'].items():
                model_info = self._models_info.setdefault(model_name, {})
                if "fields" not in model_info:
                    model_info["fields"] = {}
                model_info["fields"].update(value["fields"])

        # pick the first editable subview
        view_type = next(
            vtype for vtype in node.get('mode', 'list').split(',') if vtype != 'form'
        )
        if not (view_type == 'list' and views['list'].get('editable')):
            view_type = 'form'

        # don't recursively process o2ms in o2ms
        return self._process_view(views[view_type], submodel, level=level-1)