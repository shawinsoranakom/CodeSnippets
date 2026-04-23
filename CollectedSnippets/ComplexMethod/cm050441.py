def set_values(self):
        group_use_lead_id = self.env['ir.model.data']._xmlid_to_res_id('crm.group_use_lead')
        has_group_lead_before = group_use_lead_id in self.env.user.all_group_ids.ids
        super(ResConfigSettings, self).set_values()
        # update use leads / opportunities setting on all teams according to settings update
        has_group_lead_after = group_use_lead_id in self.env.user.all_group_ids.ids
        if has_group_lead_before != has_group_lead_after:
            teams = self.env['crm.team'].search([])
            teams.filtered('use_opportunities').use_leads = has_group_lead_after
            for team in teams:
                team.alias_id.write(team._alias_get_creation_values())
        # synchronize cron with settings
        assign_cron = self.sudo().env.ref('crm.ir_cron_crm_lead_assign', raise_if_not_found=False)
        if assign_cron:
            # Writing on a cron tries to grab a write-lock on the table. This
            # could be avoided when saving a res.config without modifying this specific
            # configuration
            cron_vals = {
                'active': self.crm_use_auto_assignment and self.crm_auto_assignment_action == 'auto',
                'interval_type': self.crm_auto_assignment_interval_type,
                'interval_number': self.crm_auto_assignment_interval_number,
                # keep nextcall on cron as it is required whatever the setting
                'nextcall': self.crm_auto_assignment_run_datetime if self.crm_auto_assignment_run_datetime else assign_cron.nextcall,
            }
            cron_vals = {field_name: value for field_name, value in cron_vals.items() if assign_cron[field_name] != value}
            if cron_vals:
                assign_cron.write(cron_vals)