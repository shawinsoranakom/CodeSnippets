def _handle_won_lost(self, old_status_by_lead, new_status_by_lead):
        """ This method handles all changes of won / lost status of leads on creation / writing,
        and update the scoring frequency table accordingly:
        - To lost : Increment corresponding lost count
        - To won : Increment corresponding won count
        - Leaving lost : Decrement corresponding lost count
        - Leaving won : Decrement corresponding won count
        More than one operation can happen simultaneously, for instance, going from lost to won:
        Decrement corresponding lost count + increment corresponding won count.

        A lead is WON when in won stage (and probability = 100% but that is implied and constrained)
        A lead is LOST when active = False AND probability = 0
        In every other case, the lead is not won nor lost.

        :param old_status_by_lead: dict of old status by lead: {lead.id: {'is_lost': ..., 'is_won': ...}}
        :param new_status_by_lead: dict of new status by lead: {lead.id: {'is_lost': ..., 'is_won': ...}}
        """
        leads_reach_won_ids = self.env['crm.lead']
        leads_leave_won_ids = self.env['crm.lead']
        leads_reach_lost_ids = self.env['crm.lead']
        leads_leave_lost_ids = self.env['crm.lead']

        for lead in self:
            new_status = new_status_by_lead.get(
                lead.id, {'is_lost': False, 'is_won': False}
            )
            old_status = old_status_by_lead.get(
                lead.id, {'is_lost': False, 'is_won': False}
            )
            if new_status['is_lost'] and new_status['is_won']:
                raise ValidationError(_("The lead %s cannot be won and lost at the same time.", lead))

            if new_status['is_lost'] and not old_status['is_lost']:
                leads_reach_lost_ids += lead
            elif not new_status['is_lost'] and old_status['is_lost']:
                leads_leave_lost_ids += lead

            if new_status['is_won'] and not old_status['is_won']:
                leads_reach_won_ids += lead
            elif not new_status['is_won'] and old_status['is_won']:
                leads_leave_won_ids += lead

        leads_reach_won_ids._pls_increment_frequencies(to_state='won')
        leads_leave_won_ids._pls_increment_frequencies(from_state='won')
        leads_reach_lost_ids._pls_increment_frequencies(to_state='lost')
        leads_leave_lost_ids._pls_increment_frequencies(from_state='lost')

        return True