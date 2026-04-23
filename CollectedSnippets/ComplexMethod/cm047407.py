def _get_view(self, view_id=None, view_type='form', **options):
        """
        Get the model view combined architecture (the view along all its
        inheriting views).

        :param view_id: id of the view or None
        :type view_id: int or None
        :param str view_type: type of the view to return if view_id is None,
            one of ``'form'``, ``'list'``, ...
        :param options: options to return additional features

            :param bool mobile: true if the web client is currently using the
                responsive mobile view (to use kanban views instead of list
                views for x2many fields)

        :return: architecture of the view as an etree node, and the browse
            record of the view used
        :rtype: tuple
        :raise AttributeError: if no view exists for that model, and no method
            ``_get_default_<view_type>_view`` exists for the view type
        """
        IrUiView = self.env['ir.ui.view'].sudo()

        # try to find a view_id if none provided
        if not view_id:
            # <view_type>_view_ref in context can be used to override the default view
            view_ref_key = view_type + '_view_ref'
            view_ref = self.env.context.get(view_ref_key)
            if view_ref:
                if '.' in view_ref:
                    module, view_ref = view_ref.split('.', 1)

                    sql = SQL(
                        "SELECT res_id FROM ir_model_data WHERE model='ir.ui.view' AND module=%s AND name=%s",
                        module, view_ref,
                    )
                    if view_ref_res := self.env.execute_query(sql):
                        [[view_id]] = view_ref_res
                else:
                    _logger.warning(
                        '%r requires a fully-qualified external id (got: %r for model %s). '
                        'Please use the complete `module.view_id` form instead.', view_ref_key, view_ref,
                        self._name
                    )

            if not view_id:
                # otherwise try to find the lowest priority matching ir.ui.view
                view_id = IrUiView.default_view(self._name, view_type)

        if view_id:
            # read the view with inherited views applied
            view = IrUiView.browse(view_id)
            arch = view._get_combined_arch()
        else:
            # fallback on default views methods if no ir.ui.view could be found
            view = IrUiView.browse()
            try:
                arch = getattr(self, '_get_default_%s_view' % view_type)()
            except AttributeError:
                raise UserError(_("No default view of type '%s' could be found!", view_type))
        return arch, view