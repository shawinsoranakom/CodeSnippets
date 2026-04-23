def write(self, vals):
        requisitions_to_rename = self.env['purchase.requisition']
        if 'requisition_type' in vals or 'company_id' in vals:
            requisitions_to_rename = self.filtered(lambda r:
                r.requisition_type != vals.get('requisition_type', r.requisition_type) or
                r.company_id.id != vals.get('company_id', r.company_id.id))
        res = super().write(vals)
        for requisition in requisitions_to_rename:
            if requisition.state != 'draft':
                raise UserError(_("You cannot change the Agreement Type or Company of a not draft purchase agreement."))
            if requisition.requisition_type == 'purchase_template':
                requisition.date_start = requisition.date_end = False
            code = requisition.requisition_type == 'blanket_order' and 'purchase.requisition.blanket.order' or 'purchase.requisition.purchase.template'
            requisition.name = self.env['ir.sequence'].with_company(requisition.company_id).next_by_code(code)
        return res