def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        context_location = self.env.context.get('location') or self.env.context.get('search_location')
        if context_location and isinstance(context_location, int):
            location = self.env['stock.location'].browse(context_location)
            if location.usage == 'supplier':
                if res.get('virtual_available'):
                    res['virtual_available']['string'] = _('Future Receipts')
                if res.get('qty_available'):
                    res['qty_available']['string'] = _('Received Qty')
            elif location.usage == 'internal':
                if res.get('virtual_available'):
                    res['virtual_available']['string'] = _('Forecasted Quantity')
            elif location.usage == 'customer':
                if res.get('virtual_available'):
                    res['virtual_available']['string'] = _('Future Deliveries')
                if res.get('qty_available'):
                    res['qty_available']['string'] = _('Delivered Qty')
            elif location.usage == 'inventory':
                if res.get('virtual_available'):
                    res['virtual_available']['string'] = _('Future P&L')
                if res.get('qty_available'):
                    res['qty_available']['string'] = _('P&L Qty')
            elif location.usage == 'production':
                if res.get('virtual_available'):
                    res['virtual_available']['string'] = _('Future Productions')
                if res.get('qty_available'):
                    res['qty_available']['string'] = _('Produced Qty')
        return res