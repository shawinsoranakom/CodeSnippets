def _compute_subject(self):
        """ Computation is coming either form template, either from context.
        When having a template with a value set, copy it (in batch mode) or
        render it (in monorecord comment mode) on the composer. Otherwise
        it comes from the parent (if set), or computed based on the generic
        '_message_compute_subject' method or to the record display_name in
        monorecord comment mode, or set to False. When removing the template,
        reset it. """
        for composer in self:
            if composer.template_id:
                composer._set_value_from_template('subject')
            if not composer.template_id or not composer.subject:
                subject = composer.parent_id.subject
                if (not subject and composer.model and
                    composer.composition_mode == 'comment' and
                    not composer.composition_batch):
                    res_ids = composer._evaluate_res_ids()
                    if composer.model_is_thread:
                        subject = self.env[composer.model].browse(res_ids)._message_compute_subject()
                    else:
                        subject = self.env[composer.model].browse(res_ids).display_name
                composer.subject = subject