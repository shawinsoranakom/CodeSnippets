def _render_template_inline_template(self, template_txt, model, res_ids,
                                         add_context=None, options=None):
        """ Render a string-based template on records given by a model and a list
        of IDs, using inline_template.

        In addition to the generic evaluation context available, some other
        variables are added:
          * ``object``: record based on which the template is rendered;

        :param str template_txt: template text to render
        :param str model: see ``MailRenderMixin._render_template()``;
        :param list res_ids: see ``MailRenderMixin._render_template()``;

        :param dict add_context: additional context to give to renderer. It
          allows to add or update values to base rendering context generated
          by ``MailRenderMixin._render_inline_template_eval_context()``;
        :param dict options: options for rendering (no options available
          currently);

        :returns: {res_id: string of rendered template based on record}
        :rtype: dict
        """
        results = dict.fromkeys(res_ids, "")
        if not template_txt or not res_ids:
            return results

        if not self._has_unsafe_expression_template_inline_template(str(template_txt), model):
            # do not call the qweb engine
            return self._render_template_inline_template_regex(str(template_txt), model, res_ids)

        if (not self._unrestricted_rendering
            and not self.env.is_admin()
            and not self.env.user.has_group('mail.group_mail_template_editor')):
            group = self.env.ref('mail.group_mail_template_editor')
            raise AccessError(
                _('Only members of %(group_name)s group are allowed to edit templates containing sensible placeholders',
                  group_name=group.name)
            )

        # prepare template variables
        variables = self._render_eval_context()
        if add_context:
            variables.update(**add_context)

        for record in self.env[model].browse(res_ids):
            variables['object'] = record

            try:
                results[record.id] = render_inline_template(
                    parse_inline_template(str(template_txt)),
                    variables
                )
            except Exception as e:
                _logger.info("Failed to render inline_template: \n%s", str(template_txt), exc_info=True)
                raise UserError(
                    _("Failed to render inline_template template: %(template_txt)s\n"
                    "Error details: %(error)s",
                    template_txt=template_txt,
                    error=str(e))
                ) from e

        return results