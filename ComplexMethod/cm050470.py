def create(self, vals_list):
        for vals in vals_list:
            order = self.env['pos.order'].browse(vals['order_id']) if vals.get('order_id') else False
            if order and order.exists() and not vals.get('name'):
                # set name based on the sequence specified on the config
                config = order.session_id.config_id
                if config.order_line_seq_id:
                    vals['name'] = config.order_line_seq_id._next()
            if not vals.get('name'):
                # fallback on any pos.order sequence
                vals['name'] = self.env['ir.sequence'].next_by_code('pos.order.line')
        return super().create(vals_list)