def _set_value_from_template(self, template_fname, composer_fname=False):
        """ Set composer value from its template counterpart. In monorecord
        comment mode, we get directly the rendered value, giving the real
        value to the user. Otherwise we get the raw (unrendered) value from
        template, as it will be rendered at send time (for mass mail, whatever
        the number of contextual records to mail) or before posting on records
        (for comment in batch).

        :param str template_fname: name of field on template model, used to
          fetch the value (and maybe render it);
        :param str composer_fname: name of field on composer model, when field
          names do not match (e.g. body_html on template used to populate body
          on composer);
        """
        self.ensure_one()
        composer_fname = composer_fname or template_fname

        # fetch template value, check if void
        template_value = self.template_id[template_fname] if self.template_id else False
        if template_value and template_fname == 'body_html':
            template_value = template_value if not is_html_empty(template_value) else False

        if template_value:
            if self.composition_mode == 'comment' and not self.composition_batch:
                res_ids = self._evaluate_res_ids()
                rendering_res_ids = res_ids or [0]
                self[composer_fname] = self.template_id._generate_template(
                    rendering_res_ids,
                    {template_fname},
                    # monorecord comment -> ok to use suggested recipients
                    recipients_allow_suggested=(
                        self.message_type == 'comment' and not self.subtype_is_log
                    ),
                )[rendering_res_ids[0]][template_fname]
            else:
                self[composer_fname] = self.template_id[template_fname]
        return self[composer_fname]