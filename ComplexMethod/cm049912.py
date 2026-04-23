def _get_warning_messages(self):
        warnings = super()._get_warning_messages()

        if self.activity_date_deadline_range < 0:
            warnings.append(_("The 'Due Date In' value can't be negative."))

        if self.state == 'mail_post' and self.template_id and self.template_id.model_id != self.model_id:
            warnings.append(_("Mail template model of $(action_name)s does not match action model.", action_name=self.name))

        if self.state in {'mail_post', 'followers', 'remove_followers', 'next_activity'} and self.model_id.transient:
            warnings.append(_("This action cannot be done on transient models."))

        if (
            (self.state in {"followers", "remove_followers"}
            or (self.state == "mail_post" and self.mail_post_method != "email"))
            and not self.model_id.is_mail_thread
        ):
            warnings.append(_("This action can only be done on a mail thread models"))

        if self.state == 'next_activity' and not self.model_id.is_mail_activity:
            warnings.append(_("A next activity can only be planned on models that use activities."))

        if self.state in ('followers', 'remove_followers') and self.followers_type == 'generic' and self.followers_partner_field_name:
            fields, field_chain_str = self._get_relation_chain("followers_partner_field_name")
            if fields and fields[-1].comodel_name != "res.partner":
                warnings.append(_(
                    "The field '%(field_chain_str)s' is not a partner field.",
                    field_chain_str=field_chain_str,
                ))

        if self.state == 'next_activity' and self.activity_user_type == 'generic' and self.activity_user_field_name:
            fields, field_chain_str = self._get_relation_chain("activity_user_field_name")
            if fields and fields[-1].comodel_name != "res.users":
                warnings.append(_(
                    "The field '%(field_chain_str)s' is not a user field.",
                    field_chain_str=field_chain_str,
                ))

        return warnings