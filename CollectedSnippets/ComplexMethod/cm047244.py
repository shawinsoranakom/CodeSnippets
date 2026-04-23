def write(self, vals):
        res = super().write(vals)
        if 'company_ids' not in vals:
            return res
        group_multi_company_id = self.env['ir.model.data']._xmlid_to_res_id(
            'base.group_multi_company', raise_if_not_found=False)
        if group_multi_company_id:
            for user in self:
                company_count = len(user.sudo().company_ids)
                if company_count <= 1 and group_multi_company_id in user.group_ids.ids:
                    user.write({'group_ids': [Command.unlink(group_multi_company_id)]})
                elif company_count > 1 and group_multi_company_id not in user.group_ids.ids:
                    user.write({'group_ids': [Command.link(group_multi_company_id)]})
        return res