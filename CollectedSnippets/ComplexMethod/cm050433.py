def _track_subtype(self, init_values):
        self.ensure_one()
        if 'stage_id' in init_values and self.won_status == 'won':
            return self.env.ref('crm.mt_lead_won')
        elif 'lost_reason_id' in init_values and self.lost_reason_id:
            return self.env.ref('crm.mt_lead_lost')
        elif 'stage_id' in init_values:
            return self.env.ref('crm.mt_lead_stage')
        elif 'won_status' in init_values and self.won_status != 'lost':
            return self.env.ref('crm.mt_lead_restored')
        elif 'won_status' in init_values and self.won_status == 'lost':
            return self.env.ref('crm.mt_lead_lost')
        return super()._track_subtype(init_values)