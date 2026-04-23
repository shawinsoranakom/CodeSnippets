def action_set_won(self):
        """ Won semantic: stage.is_won (AND probability = 100 but implied) """
        self.action_unarchive()
        # group the leads by team_id, in order to write once by values couple (each write leads to frequency increment)
        leads_by_won_stage = {}
        for lead in self:
            won_stages = self._stage_find(domain=[('is_won', '=', True)], limit=None)
            # ABD : We could have a mixed pipeline, with "won" stages being separated by "standard"
            # stages. In the future, we may want to prevent any "standard" stage to have a higher
            # sequence than any "won" stage. But while this is not the case, searching
            # for the "won" stage while alterning the sequence order (see below) will correctly
            # handle such a case :
            #       stage sequence : [x] [x (won)] [y] [y (won)] [z] [z (won)]
            #       when in stage [y] and marked as "won", should go to the stage [y (won)],
            #       not in [x (won)] nor [z (won)]
            stage_id = next((stage for stage in won_stages if stage.sequence > lead.stage_id.sequence), None)
            if not stage_id:
                stage_id = next((stage for stage in reversed(won_stages) if stage.sequence <= lead.stage_id.sequence), won_stages)
            if stage_id in leads_by_won_stage:
                leads_by_won_stage[stage_id] += lead
            else:
                leads_by_won_stage[stage_id] = lead
        for won_stage_id, leads in leads_by_won_stage.items():
            leads.write({'stage_id': won_stage_id.id, 'probability': 100})
        return True