def _render_encapsulate(self, layout_xmlid, html, add_context=None, context_record=None):
        """ Encapsulate html content (i.e. an email body) in a layout containing
        more complex html. Used to generate a 'email friendly' content from
        simple html content.

        Typical usage: encapsulate content in email layouts like 'mail_notification_layout'
        or 'mail_notification_light'. Also used for digest layouts. This leads
        to some default rendering values being computed here, often used in those
        templates. """
        record_name = (add_context or {}).get('record_name', context_record.display_name if context_record else '')
        subtype = (add_context or {}).get('subtype', self.env['mail.message.subtype'].sudo())
        template_ctx = {
            'body': html,
            'record': context_record,
            'record_name': record_name,
            **(add_context or {}),
        }
        # the 'mail_notification_light' expects a mail.message 'message' context, let's give it one
        if not template_ctx.get('message'):
            msg_vals = {'body': html}
            if context_record:
                msg_vals.update({'model': context_record._name, 'res_id': context_record.id})
            template_ctx['message'] = self.env['mail.message'].sudo().new(msg_vals)
        # other message info
        if not subtype:
            template_ctx['is_discussion'] = False
            template_ctx['subtype_internal'] = False
        else:
            if 'is_discussion' not in template_ctx:
                template_ctx['is_discussion'] = subtype.id == self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
            if 'subtype_internal' not in template_ctx:
                template_ctx['subtype_internal'] = subtype.is_internal
        template_ctx.setdefault('subtype', subtype)
        template_ctx.setdefault('tracking_values', [])
        # record info
        if 'model_description' not in template_ctx:
            template_ctx['model_description'] = self.env['ir.model']._get(context_record._name).display_name if context_record else False
        template_ctx.setdefault('subtitles', [record_name])
        # user / environment
        template_ctx.setdefault('author_user', False)
        if 'company' not in template_ctx:
            template_ctx['company'] = context_record._mail_get_companies(default=self.env.company)[context_record.id] if context_record else self.env.company
        template_ctx.setdefault('email_add_signature', False)
        template_ctx.setdefault('lang', self.env.lang)
        template_ctx.setdefault('signature', '')
        template_ctx.setdefault('show_unfollow', False)
        template_ctx.setdefault('website_url', '')
        # display: actions / buttons
        template_ctx.setdefault('button_access', False)
        template_ctx.setdefault('has_button_access', False)
        # display
        template_ctx.setdefault('email_notification_force_header', self.env.context.get('email_notification_force_header', False))
        template_ctx.setdefault('email_notification_force_footer', self.env.context.get('email_notification_force_footer', False))
        template_ctx.setdefault('email_notification_allow_header', self.env.context.get('email_notification_allow_header', True))
        template_ctx.setdefault('email_notification_allow_footer', self.env.context.get('email_notification_allow_footer', False))
        # tools
        template_ctx.setdefault('is_html_empty', is_html_empty)

        html = self.env['ir.qweb']._render(layout_xmlid, template_ctx, minimal_qcontext=True, raise_if_not_found=False)
        if not html:
            _logger.warning('QWeb template %s not found when rendering encapsulation template.' % (layout_xmlid))
        html = self.env['mail.render.mixin']._replace_local_links(html)
        return html