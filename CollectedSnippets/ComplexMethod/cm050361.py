def write(self, vals):
        if vals.get('purchase_group_id', False):
            # store in case linking to a PO with existing linkages
            orig_purchase_group = self.purchase_group_id
        result = super(PurchaseOrder, self).write(vals)
        if vals.get('requisition_id'):
            for order in self:
                order.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': order, 'origin': order.requisition_id, 'edit': True},
                    subtype_xmlid='mail.mt_note',
                )
        if vals.get('alternative_po_ids', False):
            if not self.purchase_group_id and len(self.alternative_po_ids + self) > len(self):
                # this can create a new group + delete an existing one (or more) when linking to already linked PO(s), but this is
                # simplier than additional logic checking if exactly 1 exists or merging multiple groups if > 1
                self.env['purchase.order.group'].create({'order_ids': [Command.set(self.ids + self.alternative_po_ids.ids)]})
            elif self.purchase_group_id and len(self.alternative_po_ids + self) <= 1:
                # write in purchase group isn't called so we have to manually unlink obsolete groups here
                self.purchase_group_id.unlink()
        if vals.get('purchase_group_id', False):
            # the write is for multiple POs => don't double count the POs of the final group
            additional_groups = orig_purchase_group - self.purchase_group_id
            if additional_groups:
                additional_pos = (additional_groups.order_ids - self.purchase_group_id.order_ids)
                additional_groups.unlink()
                if additional_pos:
                    self.purchase_group_id.order_ids |= additional_pos

        return result