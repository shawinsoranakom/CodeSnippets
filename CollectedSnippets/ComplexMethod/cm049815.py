def _generate_template_static_values(self, res_ids, render_fields, render_results=None):
        """ Return values based on template 'self'. Those are not rendered nor
        dynamic, just static values used for configuration of emails.

        :param list res_ids: list of record IDs on which template is rendered;
        :param list render_fields: list of fields to render, currently limited
          to a subset (i.e. auto_delete, mail_server_id, model, res_id);
        :param dict render_results: res_ids-based dictionary of render values.
          For each res_id, a dict of values based on render_fields is given;

        :return: updated (or new) render_results;
        """
        self.ensure_one()
        if render_results is None:
            render_results = {}

        for res_id in res_ids:
            values = render_results.setdefault(res_id, {})

            # technical settings
            if 'auto_delete' in render_fields:
                values['auto_delete'] = self.auto_delete
            if 'email_layout_xmlid' in render_fields:
                values['email_layout_xmlid'] = self.email_layout_xmlid
            if 'mail_server_id' in render_fields:
                values['mail_server_id'] = self.mail_server_id.id
            if 'model' in render_fields:
                values['model'] = self.model
            if 'res_id' in render_fields:
                values['res_id'] = res_id or False

        return render_results