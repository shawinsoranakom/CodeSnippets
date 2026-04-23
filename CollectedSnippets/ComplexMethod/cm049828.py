def _render_template_qweb(self, template_src, model, res_ids,
                              add_context=None, options=None):
        """ Render a raw QWeb template.

        In addition to the generic evaluation context available, some other
        variables are added:
          * ``object``: record based on which the template is rendered;

        :param str template_src: raw QWeb template to render;
        :param str model: see ``MailRenderMixin._render_template()``;
        :param list res_ids: see ``MailRenderMixin._render_template()``;

        :param dict add_context: additional context to give to renderer. It
          allows to add or update values to base rendering context generated
          by ``MailRenderMixin._render_eval_context()``;
        :param dict options: options for rendering propagated to IrQweb render
          (see docstring for available options);

        :returns: {res_id: string of rendered template based on record}
        :rtype: dict
        """
        results = dict.fromkeys(res_ids, u"")
        if not template_src or not res_ids:
            return results

        if not self._has_unsafe_expression_template_qweb(template_src, model):
            # do not call the qweb engine
            return self._render_template_qweb_regex(template_src, model, res_ids)

        # prepare template variables
        variables = self._render_eval_context()
        if add_context:
            variables.update(**add_context)

        is_restricted = not self._unrestricted_rendering and not self.env.is_admin() and not self.env.user.has_group('mail.group_mail_template_editor')

        for record in self.env[model].browse(res_ids):
            variables['object'] = record
            options = options or {}
            if is_restricted:
                options['raise_on_forbidden_code_for_model'] = model
            try:
                render_result = self.env['ir.qweb']._render(
                    html.fragment_fromstring(template_src, create_parent='div'),
                    variables,
                    **options,
                )
                # remove the rendered tag <div> that was added in order to wrap potentially multiples nodes into one.
                render_result = render_result[5:-6]
            except Exception as e:
                if isinstance(e, QWebError) and isinstance(e.__cause__, PermissionError):
                    group = self.env.ref('mail.group_mail_template_editor')
                    raise AccessError(
                        _('Only members of %(group_name)s group are allowed to edit templates containing sensible placeholders',
                           group_name=group.name)
                    ) from e
                elif isinstance(e, QWebError):
                    # We extract the message before the template dump to clean out the full template
                    # source, since it will be added later again
                    error_details = str(e).split('\nTemplate:')[0].strip()
                else:
                    error_details = str(e)
                error_traceback = traceback.format_exc()

                # Identify the template safely
                template_label = _("Template name not identified")

                if self._name == 'mail.template' and self.id:
                    template_label = _("Mail Template: '%(name)s' (ID: %(record_id)s)",
                                       name=self.name or _("Unnamed Mail Template"),
                                       record_id=self.id)
                    is_identified = True
                elif self._name == 'mail.compose.message' and self.mass_mailing_id:
                    template_label = _("Mass Mailing Template: '%(name)s' (ID: %(record_id)s)",
                                       name=self.mass_mailing_id.display_name or _("Unnamed Mailing"),
                                       record_id=self.mass_mailing_id.id)
                    is_identified = True
                else:
                    # if we can't name the template, we output the full template src, so that we
                    # can try to find the failing template by it's src
                    template_label = _("Template name not identified")
                    is_identified = False

                # Truncation of the source to prevent log bloat
                truncated_src = template_src
                if len(template_src) > 1000 and is_identified:
                    truncated_src = f"{template_src[:500]}\n[...] (content truncated) [...]\n{template_src[-500:]}"

                lang_context = self.env.context.get('lang', _("No language detected in context"))
                _logger.error(
                    "Failed to render QWeb template for %s - Context language:%s\nTarget Model: %s\nError: %s\n%s",
                    template_label, lang_context, model, error_details, truncated_src
                )
                # Log the full technical traceback for the sysadmin/developer
                _logger.debug(
                    "Failed to render QWeb template for %s - Context language:%s\nTarget Model: %s\nError: %s\n%s",
                    template_label, lang_context, model, error_details, error_traceback
                )

                # Raise a cleaner error for the UI
                raise UserError(
                    _("Failed to render QWeb template for %(template_label)s\n"
                    "Target Model: %(model_name)s\n"
                    "Language context: %(lang_context)s\n"
                    "Error: %(error_details)s\n\n"
                    "Template Source Snippet:\n%(template_src)s",
                    template_label=template_label,
                    model_name=model,
                    lang_context=lang_context,
                    error_details=error_details,
                    template_src=truncated_src)
                ) from e
            results[record.id] = render_result

        return results