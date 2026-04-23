def _get_cached_template_info(self, id_or_xmlid, _view=None):
        """ Return the ir.ui.view id from the xml id, use `_preload_views`.
        """
        view = None
        error = False
        if _view is not None:
            view = _view
        elif isinstance(id_or_xmlid, int):
            view = self.env['ir.ui.view'].sudo().browse(id_or_xmlid)
            try:
                view.key
            except MissingError:
                view = None
                error = MissingError(self.env._("Template not found: '%s'", id_or_xmlid))
            except UserError as e:
                view = None
                error = e
        else:
            preload = self.sudo()._preload_views([id_or_xmlid])
            if id_or_xmlid in preload:
                info = preload[id_or_xmlid]
                view = info['view']
                error = info['error']
            else:
                error = SyntaxError('Error compiling template')
        info = {
            f: view[f] if view else None
            for f in self._get_cached_template_prefetched_keys()}
        info['error'] = error
        return info