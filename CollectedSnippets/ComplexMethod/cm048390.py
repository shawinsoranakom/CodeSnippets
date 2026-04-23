def _compute_next_inventory_date(self):
        for location in self:
            if location.company_id and location.usage in ['internal', 'transit'] and location.cyclic_inventory_frequency > 0:
                try:
                    if location.last_inventory_date:
                        days_until_next_inventory = location.cyclic_inventory_frequency - (fields.Date.today() - location.last_inventory_date).days
                        if days_until_next_inventory <= 0:
                            location.next_inventory_date = fields.Date.today() + timedelta(days=1)
                        else:
                            location.next_inventory_date = location.last_inventory_date + timedelta(days=location.cyclic_inventory_frequency)
                    else:
                        location.next_inventory_date = fields.Date.today() + timedelta(days=location.cyclic_inventory_frequency)
                except OverflowError:
                    raise UserError(_("The selected Inventory Frequency (Days) creates a date too far into the future."))
            else:
                location.next_inventory_date = False