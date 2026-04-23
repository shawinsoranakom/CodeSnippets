def _merge_opportunity(self, user_id=False, team_id=False, auto_unlink=True, max_length=5):
        """ Private merging method. This one allows to relax rules on record set
        length allowing to merge more than 5 opportunities at once if requested.
        This should not be called by action buttons.

        See ``merge_opportunity`` for more details. """
        if len(self.ids) <= 1:
            raise UserError(_('Select at least two Leads/Opportunities from the list to merge them.'))

        if max_length and len(self.ids) > max_length and not self.env.is_superuser():
            raise UserError(_("To prevent data loss, Leads and Opportunities can only be merged by groups of %(max_length)s.", max_length=max_length))

        opportunities = self._sort_by_confidence_level(reverse=True)

        # get SORTED recordset of head and tail, and complete list
        opportunities_head = opportunities[0]
        opportunities_tail = opportunities[1:]

        # merge all the sorted opportunity. This means the value of
        # the first (head opp) will be a priority.
        merged_data = opportunities._merge_data(self._merge_get_fields())

        # force value for saleperson and Sales Team
        if user_id:
            merged_data['user_id'] = user_id
        if team_id:
            merged_data['team_id'] = team_id

        merged_followers = opportunities_head._merge_followers(opportunities_tail)

        # log merge message
        opportunities_head._merge_log_summary(merged_followers, opportunities_tail)
        # merge other data (mail.message, attachments, ...) from tail into head
        opportunities_head._merge_dependences(opportunities_tail)

        # check if the stage is in the stages of the Sales Team. If not, assign the stage with the lowest sequence
        if merged_data.get('team_id'):
            team_stage_ids = self.env['crm.stage'].search(['|', ('team_ids', 'in', merged_data['team_id']), ('team_ids', '=', False)], order='sequence, id')
            if merged_data.get('stage_id') not in team_stage_ids.ids:
                merged_data['stage_id'] = team_stage_ids[0].id if team_stage_ids else False

        # write merged data into first opportunity; remove some keys if already
        # set on opp to avoid useless recomputes
        if 'user_id' in merged_data and opportunities_head.user_id.id == merged_data['user_id']:
            merged_data.pop('user_id')
        if 'team_id' in merged_data and opportunities_head.team_id.id == merged_data['team_id']:
            merged_data.pop('team_id')
        opportunities_head.write(merged_data)

        # delete tail opportunities
        # we use the SUPERUSER to avoid access rights issues because as the user had the rights to see the records it should be safe to do so
        if auto_unlink:
            opportunities_tail.sudo().unlink()

        return opportunities_head