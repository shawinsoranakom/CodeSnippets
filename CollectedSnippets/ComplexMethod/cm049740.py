def _compute_partner_ids(self):
        """ Computation is coming either from template, either from context.
        When having a template it uses its 3 fields 'email_cc', 'email_to' and
        'partner_to', in monorecord comment mode. Emails are converted into
        partners, creating new ones when the email does not match any existing
        partner. Composer does not deal with emails but only with partners.
        When having a template in other modes, no recipients are computed
        as it is done at sending time. When removing the template, reset it.

        When not having a template, recipients may come from the parent in
        comment mode, to be sure to notify the same people. """
        for composer in self:
            template = composer.template_id
            # Use template in comment mode only if there are no partners yet or if the template specifies different ones
            # as suggested recipients should normally not change and we don't want to re-add them every time
            if (template and composer.composition_mode == 'comment'
                and not composer.composition_batch
                and (not template.use_default_to or not composer.partner_ids)
            ):
                res_ids = composer._evaluate_res_ids() or [0]
                rendered_values = composer._generate_template_for_composer(
                    res_ids,
                    {'email_cc', 'email_to', 'partner_ids'},
                    allow_suggested=composer.message_type == 'comment' and not composer.subtype_is_log,
                    find_or_create_partners=True,
                )[res_ids[0]]
                if rendered_values.get('partner_ids'):
                    composer.partner_ids = rendered_values['partner_ids']
            elif composer.parent_id and composer.composition_mode == 'comment':
                composer.partner_ids = composer.parent_id.partner_ids
            elif not composer.template_id:
                composer.partner_ids = False