def _get_gs1_barcode(self, gs1_quantity_rules_ai_by_uom=False):
        """ Generates a GS1 barcode for the quant's properties (product, quantity and LN/SN.)

        :param gs1_quantity_rules_ai_by_uom: contains the products' GS1 AI paired with the UoM id
        :type gs1_quantity_rules_ai_by_uom: dict
        :return: str
        """
        self.ensure_one()
        gs1_quantity_rules_ai_by_uom = gs1_quantity_rules_ai_by_uom or {}
        barcode = ''

        # Product part.
        if self.product_id.valid_ean:
            barcode = self.product_id.barcode
            barcode = '01' + '0' * (14 - len(barcode)) + barcode
        elif self.tracking == 'none' or not self.lot_id:
            return ''  # Doesn't make sense to generate a GS1 barcode for qty with no other data.

        # Quantity part.
        if self.tracking != 'serial' or self.quantity > 1:
            quantity_ai = gs1_quantity_rules_ai_by_uom.get(self.product_uom_id.id)
            if quantity_ai:
                qty_str = str(int(self.quantity / self.product_uom_id.rounding))
                if len(qty_str) <= 6:
                    barcode += quantity_ai + '0' * (6 - len(qty_str)) + qty_str
            else:
                # No decimal indicator for GS1 Units, no better solution than rounding the qty.
                qty_str = str(int(round(self.quantity)))
                if len(qty_str) <= 8:
                    barcode += '30' + '0' * (8 - len(qty_str)) + qty_str

        # Tracking part (must be GS1 barcode's last part since we don't know SN/LN length.)
        if self.lot_id:
            if len(self.lot_id.name) > 20:
                # Cannot generate a valid GS1 barcode since the lot/serial number max length is
                # exceeded and this information is required if the LN/SN is present.
                return ''
            tracking_ai = '21' if self.tracking == 'serial' else '10'
            barcode += tracking_ai + self.lot_id.name
        return barcode