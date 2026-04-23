def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product. We limit to 10 the number of suppliers for a product to avoid the mess that
        # could be caused for some generic products ("Miscellaneous").
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            already_seller = (partner | self.partner_id) & line.product_id.seller_ids.mapped('partner_id')
            if line.product_id and not already_seller and len(line.product_id.seller_ids) <= 10:
                price = line.price_unit
                # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
                if line.product_id.product_tmpl_id.uom_id != line.product_uom_id:
                    default_uom = line.product_id.product_tmpl_id.uom_id
                    price = line.product_uom_id._compute_price(price, default_uom)

                supplierinfo = self._prepare_supplier_info(partner, line, price, line.currency_id)
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                if line.selected_seller_id:
                    supplierinfo['product_name'] = line.selected_seller_id.product_name
                    supplierinfo['product_code'] = line.selected_seller_id.product_code
                    supplierinfo['product_uom_id'] = line.product_uom_id.id
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                # supplier info should be added regardless of the user access rights
                line.product_id.product_tmpl_id.sudo().write(vals)