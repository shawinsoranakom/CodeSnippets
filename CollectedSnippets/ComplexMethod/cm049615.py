def _prepare_frontend_environment(self, values):
        """ Update the values and context with website specific value
            (required to render website layout template)
        """
        irQweb = super()._prepare_frontend_environment(values)

        current_website = request.website
        editable = irQweb.env.user.has_group('website.group_website_designer')
        has_group_restricted_editor = irQweb.env.user.has_group('website.group_website_restricted_editor')
        if not editable and has_group_restricted_editor and 'main_object' in values:
            try:
                main_object = values['main_object'].with_user(irQweb.env.user.id)
                current_website._check_user_can_modify(main_object)
                editable = True
            except AccessError:
                pass
        translatable = has_group_restricted_editor and irQweb.env.context.get('lang') != irQweb.env['ir.http']._get_default_lang().code
        editable = editable and not translatable

        if has_group_restricted_editor and irQweb.env.user.has_group('website.group_multi_website'):
            values['multi_website_websites_current'] = lazy(lambda: current_website.name)
            values['multi_website_websites'] = lazy(lambda: [
                {'website_id': website.id, 'name': website.name, 'domain': website.domain}
                for website in current_website.search([('id', '!=', current_website.id)])
            ])

            cur_company = irQweb.env.company
            values['multi_website_companies_current'] = lazy(lambda: {'company_id': cur_company.id, 'name': cur_company.name})
            values['multi_website_companies'] = lazy(lambda: [
                {'company_id': comp.id, 'name': comp.name}
                for comp in irQweb.env.user.company_ids if comp != cur_company
            ])

        # update values

        values.update(dict(
            website=current_website,
            is_view_active=lazy(lambda: current_website.is_view_active),
            res_company=lazy(request.env['res.company'].browse(current_website._get_cached('company_id')).sudo),
            translatable=translatable,
            editable=editable,
        ))

        if editable:
            # form editable object, add the backend configuration link
            if 'main_object' in values and has_group_restricted_editor:
                func = getattr(values['main_object'], 'get_backend_menu_id', False)
                values['backend_menu_id'] = lazy(lambda: func and func() or irQweb.env['ir.model.data']._xmlid_to_res_id('website.menu_website_configuration'))

        # update options

        irQweb = irQweb.with_context(website_id=current_website.id)
        if 'inherit_branding' not in irQweb.env.context and not self.env.context.get('rendering_bundle'):
            if editable:
                # in edit mode add branding on ir.ui.view tag nodes
                irQweb = irQweb.with_context(inherit_branding=True)
            elif has_group_restricted_editor:
                # will add the branding on fields (into values)
                irQweb = irQweb.with_context(inherit_branding_auto=True)

        # Avoid cache inconsistencies: if the cookies have been accepted, the
        # DOM structure should reflect it after a reload and not be stuck in its
        # previous state (see the part related to cookies in
        # `_post_processing_att`).
        is_allowed_optional_cookies = request.env['ir.http']._is_allowed_cookie('optional')
        irQweb = irQweb.with_context(cookies_allowed=is_allowed_optional_cookies)

        return irQweb