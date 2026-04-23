def _render_field(self, field, res_ids, *args, **kwargs):
        """ Render the given field on the given records. This method enters
        sudo mode to allow qweb rendering (which is otherwise reserved for
        the 'mail template editor' group') if we consider it safe. Safe
        means content comes from the template which is a validated master
        data. As a summary the heuristic is :

          * if no template, do not bypass the check;
          * if current user is a template editor, do not bypass the check;
          * if record value and template value are the same (or equals the
            sanitized value in case of an HTML field), bypass the check;
          * for body: if current user cannot edit it, force template value back
            then bypass the check;

        Also provide support to fetch translations on the remote template.
        Indeed translations are often done on the master template, not on the
        specific composer itself. In that case we need to work on template
        value when it has not been modified in the composer. """
        if field not in self:
            raise ValueError(
                _('Rendering of %(field_name)s is not possible as not defined on template.',
                  field_name=field
                 )
            )

        if not self.template_id:
            # Do not need to bypass the verification
            return super()._render_field(field, res_ids, *args, **kwargs)

        # template-based access check + translation check
        template_field = {
            'body': 'body_html',
        }.get(field, field)
        if template_field not in self.template_id:
            raise ValueError(
                _('Rendering of %(field_name)s is not possible as no counterpart on template.',
                  field_name=field
                 )
            )

        composer_value = self[field]
        template_value = self.template_id[template_field]
        translation_asked = kwargs.get('compute_lang') or kwargs.get('set_lang')
        equality = self.body_has_template_value if field == 'body' else composer_value == template_value

        call_sudo = False
        if (not self.is_mail_template_editor and field == 'body' and
            (not self.can_edit_body or self.body_has_template_value)):
            call_sudo = True
            # take the previous body which we can trust without HTML editor reformatting
            self.body = self.template_id.body_html
        if (not self.is_mail_template_editor and field != 'body' and
              composer_value == template_value):
            call_sudo = True

        if translation_asked and equality:
            # use possibly custom lang template changed on composer instead of
            # original template one
            if not kwargs.get('res_ids_lang'):
                kwargs['res_ids_lang'] = self._render_lang(res_ids)
            template = self.template_id.sudo() if call_sudo else self.template_id
            return template._render_field(
                template_field, res_ids, *args, **kwargs,
            )

        record = self.sudo() if call_sudo else self
        return super(MailComposerMixin, record)._render_field(field, res_ids, *args, **kwargs)