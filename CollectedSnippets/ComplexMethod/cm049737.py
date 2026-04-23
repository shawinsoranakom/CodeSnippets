def _compute_attachment_ids(self):
        """ Computation is based on template and composition mode. In monorecord
        comment mode, template is used to generate attachments based on both
        attachment_ids of template, and reports coming from report_template_ids.
        Those are generated based on the current record to display. As template
        generation returns a list of tuples, new attachments are created on
        the fly during the compute.

        In batch or email mode, only attachment_ids from template are used on
        the composer. Reports will be generated at sending time.

        When template is removed, attachments are reset. """
        for composer in self:
            res_ids = composer._evaluate_res_ids() or [0]
            if (composer.template_id.attachment_ids and
                (composer.composition_mode == 'mass_mail' or composer.composition_batch)):
                composer.attachment_ids = composer.template_id.attachment_ids
            elif composer.template_id and composer.composition_mode == 'comment' and len(res_ids) == 1:
                rendered_values = composer._generate_template_for_composer(
                    res_ids,
                    ('attachment_ids', 'attachments'),
                )[res_ids[0]]
                attachment_ids = rendered_values.get('attachment_ids') or []
                # transform attachments into attachment_ids; not attached to the
                # document because this will be done further in the posting
                # process, allowing to clean database if email not send
                if rendered_values.get('attachments'):
                    attachment_ids += self.env['ir.attachment'].create([
                        {'name': attach_fname,
                         'datas': attach_datas,
                         'res_model': 'mail.compose.message',
                         'res_id': 0,
                         'type': 'binary',    # override default_type from context, possibly meant for another model!
                        } for attach_fname, attach_datas in rendered_values.pop('attachments')
                    ]).ids
                if attachment_ids:
                    composer.attachment_ids = attachment_ids
            elif not composer.template_id:
                composer.attachment_ids = False