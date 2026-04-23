def _compute_arch_diff(self):
        """ Depending of `reset_mode`, return the differences between the
        current view arch and either its previous arch, its initial arch or
        another view arch.
        """
        def get_table_name(view_id):
            name = view_id.display_name
            if view_id.key or view_id.xml_id:
                span = '<span class="ml-1 font-weight-normal small">(%s)</span>'
                name += span % (view_id.key or view_id.xml_id)
            return name

        for view in self:
            diff_to = False
            diff_to_name = False
            if view.reset_mode == 'soft':
                diff_to = view.view_id.arch_prev
                diff_to_name = _("Previous Arch")
            elif view.reset_mode == 'other_view':
                diff_to = view.compare_view_id.with_context(lang=None).arch
                diff_to_name = get_table_name(view.compare_view_id)
            elif view.reset_mode == 'hard' and view.view_id.arch_fs:
                diff_to = view.view_id.with_context(read_arch_from_file=True, lang=None).arch
                diff_to_name = _("File Arch")

            view.arch_to_compare = diff_to

            if not diff_to:
                view.arch_diff = False
                view.has_diff = False
            else:
                view_arch = view.view_id.with_context(lang=None).arch
                view.arch_diff = get_diff(
                    (view_arch, get_table_name(view.view_id) if view.reset_mode == 'other_view' else _("Current Arch")),
                    (diff_to, diff_to_name),
                    custom_style=False,
                    dark_color_scheme=request and request.cookies.get('color_scheme') == 'dark',
                )
                view.has_diff = view_arch != diff_to