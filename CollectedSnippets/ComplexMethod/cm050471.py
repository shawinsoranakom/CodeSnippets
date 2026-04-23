def write(self, vals):
        if vals.get('pack_lot_line_ids'):
            for pl in vals.get('pack_lot_ids'):
                if pl[2].get('server_id'):
                    pl[2]['id'] = pl[2]['server_id']
                    del pl[2]['server_id']
        if self.order_id.config_id.order_edit_tracking and vals.get('qty') is not None and vals.get('qty') < self.qty:
            self.is_edited = True
            body = _("%(product_name)s: Ordered quantity: %(old_qty)s", product_name=self.full_product_name, old_qty=self.qty)
            body += Markup("&rarr;") + str(vals.get('qty'))
            for line in self:
                line.order_id.message_post(body=line.order_id._prepare_pos_log(body))
        return super().write(vals)