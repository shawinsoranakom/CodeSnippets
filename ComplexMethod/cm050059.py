def _retrieve_line_vals(self, tree, document_type=False, qty_factor=1):
        """
        Read the xml invoice, extract the invoice line values, compute the odoo values
        to fill an invoice line form: quantity, price_unit, discount, product_uom_id.

        The way of computing invoice line is quite complicated:
        https://docs.peppol.eu/poacc/billing/3.0/bis/#_calculation_on_line_level (same as in factur-x documentation)

        line_net_subtotal = ( gross_unit_price - rebate ) * (delivered_qty / basis_qty) - allow_charge_amount

        with (UBL | CII):
            * net_unit_price = 'Price/PriceAmount' | 'NetPriceProductTradePrice' (mandatory) (BT-146)
            * gross_unit_price = 'Price/AllowanceCharge/BaseAmount' | 'GrossPriceProductTradePrice' (optional) (BT-148)
            * basis_qty = 'Price/BaseQuantity' | 'BasisQuantity' (optional, either below net_price node or
                gross_price node) (BT-149)
            * delivered_qty = 'InvoicedQuantity' (invoice) | 'BilledQuantity' (bill) | 'Quantity' (order) (mandatory) (BT-129)
            * allow_charge_amount = sum of 'AllowanceCharge' | 'SpecifiedTradeAllowanceCharge' (same level as Price)
                ON THE LINE level (optional) (BT-136 / BT-141)
            * line_net_subtotal = 'LineExtensionAmount' | 'LineTotalAmount' (mandatory) (BT-131)
            * rebate = 'Price/AllowanceCharge' | 'AppliedTradeAllowanceCharge' below gross_price node ! (BT-147)
                "item price discount" which is different from the usual allow_charge_amount
                gross_unit_price (BT-148) - rebate (BT-147) = net_unit_price (BT-146)

        In Odoo, we obtain:
        (1) = price_unit  =  gross_price_unit / basis_qty  =  (net_price_unit + rebate) / basis_qty
        (2) = quantity  =  delivered_qty
        (3) = discount (converted into a percentage)  =  100 * (1 - price_subtotal / (delivered_qty * price_unit))
        (4) = price_subtotal

        Alternatively, we could also set: quantity = delivered_qty/basis_qty

        WARNING, the basis quantity parameter is annoying, for instance, an invoice with a line:
            item A  | price per unit of measure/unit price: 30  | uom = 3 pieces | billed qty = 3 | rebate = 2  | untaxed total = 28
        Indeed, 30 $ / 3 pieces = 10 $ / piece => 10 * 3 (billed quantity) - 2 (rebate) = 28

        UBL ROUNDING: "the result of Item line net
            amount = ((Item net price (BT-146)÷Item price base quantity (BT-149))×(Invoiced Quantity (BT-129))
        must be rounded to two decimals, and the allowance/charge amounts are also rounded separately."
        It is not possible to do it in Odoo.
        """
        xpath_dict = self._get_line_xpaths(document_type, qty_factor)
        # basis_qty (optional)
        basis_qty = float(self._find_value(xpath_dict['basis_qty'], tree) or 1) or 1.0

        # gross_price_unit (optional)
        gross_price_unit = None
        gross_price_unit_node = tree.find(xpath_dict['gross_price_unit'])
        if gross_price_unit_node is not None:
            gross_price_unit = float(gross_price_unit_node.text)

        # net_price_unit (mandatory)
        net_price_unit = None
        net_price_unit_node = tree.find(xpath_dict['net_price_unit'])
        if net_price_unit_node is not None:
            net_price_unit = float(net_price_unit_node.text)

        # delivered_qty (mandatory)
        delivered_qty = 1
        product_vals = {k: self._find_value(v, tree) for k, v in xpath_dict['product'].items()}
        product = self._import_product(**product_vals)
        product_uom = self.env['uom.uom']
        quantity_node = tree.find(xpath_dict['delivered_qty'])
        if quantity_node is not None:
            delivered_qty = float(quantity_node.text)
            uom_xml = quantity_node.attrib.get('unitCode')
            if uom_xml:
                uom_infered_xmlid = {v: k for k, v in UOM_TO_UNECE_CODE.items()}.get(uom_xml)
                if uom_infered_xmlid:
                    product_uom = self.env.ref(uom_infered_xmlid, raise_if_not_found=False) or self.env['uom.uom']
        if product and product_uom and not product_uom._has_common_reference(product.product_tmpl_id.uom_id):
            # uom incompatibility
            product_uom = self.env['uom.uom']

        # line_net_subtotal (mandatory)
        price_subtotal = None
        line_total_amount_node = tree.find(xpath_dict['line_total_amount'])
        if line_total_amount_node is not None and line_total_amount_node.text and line_total_amount_node.text.strip():
            price_subtotal = float(line_total_amount_node.text)

        # quantity
        quantity = delivered_qty * qty_factor

        # rebate (optional)
        rebate = self._retrieve_rebate_val(tree, xpath_dict, quantity)

        # Charges are collected (they are used to create new lines), Allowances are transformed into discounts
        discount_amount, charges = self._retrieve_charge_allowance_vals(tree, xpath_dict, quantity)

        # price_unit
        charge_amount = sum(d['amount'] for d in charges)
        allow_charge_amount = discount_amount - charge_amount
        if gross_price_unit is not None:
            price_unit = gross_price_unit / basis_qty
        elif net_price_unit is not None:
            price_unit = (net_price_unit + rebate) / basis_qty
        elif price_subtotal is not None:
            price_unit = (price_subtotal + allow_charge_amount) / (delivered_qty or 1)
        else:
            price_unit = 0

        # discount
        discount = 0
        currency = self.env.company.currency_id
        if not float_is_zero(delivered_qty * price_unit, currency.decimal_places) and price_subtotal is not None:
            inferred_discount = 100 * (1 - (price_subtotal - charge_amount) / currency.round(delivered_qty * price_unit))
            discount = inferred_discount if not float_is_zero(inferred_discount, currency.decimal_places) else 0.0

        # Sometimes, the xml received is very bad; e.g.:
        #   * unit price = 0, qty = 0, but price_subtotal = -200
        #   * unit price = 0, qty = 1, but price_subtotal = -200
        #   * unit price = 1, qty = 0, but price_subtotal = -200
        # for instance, when filling a down payment as an document line. The equation in the docstring is not
        # respected, and the result will not be correct, so we just follow the simple rule below:
        if (
            net_price_unit is not None
            and price_subtotal is not None
            and float_compare(price_subtotal, net_price_unit * (delivered_qty / basis_qty) - allow_charge_amount, currency.decimal_places)
        ):
            if net_price_unit == 0 and delivered_qty == 0:
                quantity = 1
                price_unit = price_subtotal
            elif net_price_unit == 0:
                price_unit = price_subtotal / delivered_qty
            elif delivered_qty == 0:
                quantity = price_subtotal / price_unit

        return {
            # vals to be written on the document line
            'name': self._find_value(xpath_dict['name'], tree),
            'product_id': product.id,
            'product_uom_id': product_uom.id,
            'price_unit': price_unit,
            'quantity': quantity,
            'discount': discount,
            'tax_nodes': self._get_tax_nodes(tree),  # see `_retrieve_taxes`
            'charges': charges,  # see `_retrieve_line_charges`
            'price_subtotal': price_subtotal,
        }