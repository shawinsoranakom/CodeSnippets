def default_get(self, fields):
        vals = super().default_get(fields)

        # field sent by the calendar view when clicking on a date block
        # we use it to setup the scheduled date of the created mailing.mailing
        default_calendar_date = self.env.context.get('default_calendar_date')
        if default_calendar_date and ('schedule_type' in fields and 'schedule_date' in fields) \
           and Datetime.to_datetime(default_calendar_date) > Datetime.now():
            vals.update({
                'schedule_type': 'scheduled',
                'schedule_date': default_calendar_date
            })

        if 'contact_list_ids' in fields and not vals.get('contact_list_ids') and vals.get('mailing_model_id'):
            if vals.get('mailing_model_id') == self.env['ir.model']._get_id('mailing.list'):
                mailing_list = self.env['mailing.list'].search([], limit=2)
                if len(mailing_list) == 1:
                    vals['contact_list_ids'] = [(6, 0, [mailing_list.id])]
        return vals