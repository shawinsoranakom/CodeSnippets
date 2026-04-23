def assertLeadMerged(self, opportunity, leads, **expected):
        """ Assert result of lead _merge_opportunity process. This is done using
        a context manager in order to save original opportunity (master lead)
        values. Indeed those will be modified during merge process. We have to
        ensure final values are correct taking into account all leads values
        before merging them.

        :param opportunity: final opportunity
        :param leads: merged leads (including opportunity)
        """
        self.assertIn(opportunity, leads)
        opportunity = opportunity.sudo()
        leads = leads.sudo()

        # save opportunity value before being modified by merge process
        fields_all = self.FIELDS_FIRST_SET + self.merge_fields
        original_opp_values = dict(
            (fname, opportunity[fname])
            for fname in fields_all
            if fname in opportunity
        )

        def _find_value(lead, fname):
            if lead == opportunity:
                return original_opp_values[fname]
            return lead[fname]

        def _first_set(fname):
            values = [_find_value(lead, fname) for lead in leads]
            return next((value for value in values if value), False)

        def _get_type():
            values = [_find_value(lead, 'type') for lead in leads]
            return 'opportunity' if 'opportunity' in values else 'lead'

        def _get_description():
            values = [_find_value(lead, 'description') for lead in leads]
            return '<br><br>'.join(value for value in values if value)

        def _get_priority():
            values = [_find_value(lead, 'priority') for lead in leads]
            return max(values)

        def _aggregate(fname):
            if isinstance(self.env['crm.lead'][fname], models.BaseModel):
                values = leads.mapped(fname)
            else:
                values = [_find_value(lead, fname) for lead in leads]
            return values

        try:
            # merge process will modify opportunity
            yield
        finally:
            # support specific values caller may want to check in addition to generic tests
            for fname, e_val in expected.items():
                if e_val is False:
                    self.assertFalse(opportunity[fname], "%s must be False" % fname)
                else:
                    self.assertEqual(opportunity[fname], e_val, "%s must be equal to %s" % (fname, e_val))

            # classic fields: first not void wins or specific computation
            for fname in fields_all:
                if fname not in opportunity:  # not all fields available when doing -u
                    continue
                opp_value = opportunity[fname]
                if fname == 'description':
                    self.assertEqual(opp_value, _get_description())
                elif fname == 'type':
                    self.assertEqual(opp_value, _get_type())
                elif fname == 'priority':
                    self.assertEqual(opp_value, _get_priority())
                elif fname in ('order_ids', 'visitor_ids'):
                    self.assertEqual(opp_value, _aggregate(fname))
                elif fname in PARTNER_ADDRESS_FIELDS_TO_SYNC:
                    # Specific computation, has its own test
                    continue
                else:
                    self.assertEqual(
                        opp_value if opp_value or not isinstance(opp_value, models.BaseModel) else False,
                        _first_set(fname)
                    )