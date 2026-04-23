def write(self, vals):
        if vals.get('website'):
            vals['website'] = self.env['res.partner']._clean_website(vals['website'])

        now = self.env.cr.now()
        stage_updated, stage_is_won = False, False
        # stage change (or reset): update date_last_stage_update if at least one
        # lead does not have the same stage
        if 'stage_id' in vals:
            stage_updated = any(lead.stage_id.id != vals['stage_id'] for lead in self)
            if stage_updated:
                vals['date_last_stage_update'] = now
            if stage_updated and vals.get('stage_id'):
                stage = self.env['crm.stage'].browse(vals['stage_id'])
                if stage.is_won:
                    vals.update({'active': True, 'probability': 100, 'automated_probability': 100})
                    stage_is_won = True
        # user change; update date_open if at least one lead does not
        # have the same user
        if 'user_id' in vals and not vals.get('user_id'):
            vals['date_open'] = False
        elif vals.get('user_id'):
            user_updated = any(lead.user_id.id != vals['user_id'] for lead in self)
            if user_updated:
                vals['date_open'] = now

        # stage change with new stage: update probability and date_closed
        if vals.get('probability', 0) >= 100 or not vals.get('active', True):
            vals['date_closed'] = fields.Datetime.now()
        elif vals.get('probability', 0) > 0:
            vals['date_closed'] = False
        elif stage_updated and not stage_is_won and not 'probability' in vals:
            vals['date_closed'] = False

        update_frequencies = any(field in ['active', 'stage_id', 'probability'] for field in vals)
        old_status_by_lead = {
            lead.id: {
                'is_lost': lead.won_status == 'lost',
                'is_won': lead.won_status == 'won',
            } for lead in self
        } if update_frequencies else {}

        if not stage_is_won:
            result = super().write(vals)
        else:
            # stage change between two won stages: does not change the date_closed
            leads_already_won = self.filtered(lambda lead: lead.stage_id.is_won)
            remaining = self - leads_already_won
            if remaining:
                result = super(CrmLead, remaining).write(vals)
            if leads_already_won:
                vals.pop('date_closed', False)
                result = super(CrmLead, leads_already_won).write(vals)

        if update_frequencies:
            self._handle_won_lost(old_status_by_lead, {
                lead.id: {
                    'is_lost': lead.won_status == 'lost',
                    'is_won': lead.won_status == 'won',
                } for lead in self
            })

        return result