def _compute_display_name(self):
        lots_to_process_ids = []
        for lot in self:
            if lot.env.context.get('formatted_display_name') and lot.use_expiration_date and lot.expiration_date:
                name = f"{lot.name}"
                if fields.Datetime.now() >= lot.expiration_date:
                    name += self.env._("\t--Expired--")
                elif lot.alert_date and fields.Datetime.now() >= lot.alert_date:
                    name += self.env._("\t--Expire on %(date)s--", date=fields.Datetime.to_string(lot.expiration_date))
                lot.display_name = name
            else:
                lots_to_process_ids.append(lot.id)
        if lots_to_process_ids:
            super(StockLot, self.env['stock.lot'].browse(lots_to_process_ids))._compute_display_name()