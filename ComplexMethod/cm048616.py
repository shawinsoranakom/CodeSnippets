def create(self, vals_list):
        # Preprocess arguments:
        # 1. Parse lock date arguments
        #   E.g. to create an exception for 'fiscalyear_lock_date' to '2024-01-01' put
        #   {'fiscalyear_lock_date': '2024-01-01'} in the create vals.
        #   The same thing works for all other fields in SOFT_LOCK_DATE_FIELDS.
        # 2. Fetch company lock date
        for vals in vals_list:
            if 'lock_date' not in vals or 'lock_date_field' not in vals:
                # Use vals[field] (for field in SOFT_LOCK_DATE_FIELDS) to init the data
                changed_fields = [field for field in SOFT_LOCK_DATE_FIELDS if field in vals]
                if len(changed_fields) != 1:
                    raise ValidationError(_("A single exception must change exactly one lock date field."))
                field = changed_fields[0]
                vals['lock_date_field'] = field
                vals['lock_date'] = vals.pop(field)
            company = self.env['res.company'].browse(vals.get('company_id', self.env.company.id))
            if 'company_lock_date' not in vals:
                vals['company_lock_date'] = company[vals['lock_date_field']]

        exceptions = super().create(vals_list)

        # Log the creation of the exception and the changed field on the company chatter
        for exception in exceptions:
            company = exception.company_id

            # Create tracking values to display the lock date change in the chatter
            field = exception.lock_date_field
            value = exception.lock_date
            field_info = exception.fields_get([field])[field]
            tracking_values = self.env['mail.tracking.value']._create_tracking_values(
                company[field], value, field, field_info, exception,
            )
            tracking_value_ids = [Command.create(tracking_values)]

            # In case there is no explicit end datetime "forever" is implied by not mentioning an end datetime
            end_datetime_string = _(" valid until %s", format_datetime(self.env, exception.end_datetime)) if exception.end_datetime else ""
            reason_string = _(" for '%s'", exception.reason) if exception.reason else ""
            company_chatter_message = _(
                "%(exception)s for %(user)s%(end_datetime_string)s%(reason)s.",
                exception=exception._get_html_link(title=_("Exception")),
                user=exception.user_id.display_name if exception.user_id else _("everyone"),
                end_datetime_string=end_datetime_string,
                reason=reason_string,
            )
            company.sudo().message_post(
                body=company_chatter_message,
                tracking_value_ids=tracking_value_ids,
            )

        exceptions._invalidate_affected_user_lock_dates()
        return exceptions