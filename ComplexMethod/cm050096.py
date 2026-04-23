def _import_ubl_invoice_line_add_price_unit_quantity_discount(self, collected_values):
        file_document_sign = collected_values['file_document_sign']
        line_tree = collected_values['line_tree']
        currency = collected_values['currency_values']['currency']

        line_extension_amount_str = line_tree.findtext('.//{*}LineExtensionAmount')
        price_amount_str = line_tree.findtext('.//{*}Price/{*}PriceAmount')
        invoiced_quantity_str = (
            line_tree.findtext('.//{*}InvoicedQuantity')
            or line_tree.findtext('.//{*}CreditedQuantity')
        )
        base_quantity_str = line_tree.findtext('./{*}Price/{*}BaseQuantity')
        line_extension_amount = line_extension_amount_str and float(line_extension_amount_str) * file_document_sign
        price_amount = price_amount_str and float(price_amount_str)
        invoiced_quantity = invoiced_quantity_str and float(invoiced_quantity_str) * file_document_sign
        base_quantity = base_quantity_str and float(base_quantity_str) * file_document_sign

        total_allowances = sum(allowance['amount'] for allowance in collected_values['allowances'])
        total_charges = sum(charge['amount'] for charge in collected_values['charges'])
        price_allowance_values = collected_values['price_allowance_values']
        price_allowance_base_amount = price_allowance_values.get('base_amount')
        price_allowance_amount = price_allowance_values.get('amount')
        if price_allowance_amount and (price_allowance_charge_indicator_sign := price_allowance_values.get('charge_indicator_sign')):
            price_allowance_amount *= price_allowance_charge_indicator_sign
        subtotal = (line_extension_amount or 0.0) + total_allowances - total_charges

        # Price level.
        # Define at the product level the price for which quantity and how many discount you get
        # by buying it
        if price_amount:
            price_quantity = base_quantity or 1.0
            if price_allowance_base_amount:
                price_discount_amount = price_allowance_base_amount - price_amount
                price_subtotal = price_allowance_base_amount
            elif price_allowance_amount:
                price_discount_amount = -price_allowance_amount
                price_subtotal = price_amount
            else:
                price_discount_amount = 0.0
                price_subtotal = price_amount
        elif price_allowance_base_amount:
            price_subtotal = price_allowance_base_amount
            price_quantity = base_quantity or 1.0
            price_discount_amount = -(price_allowance_amount or 0.0)
        else:
            price_subtotal = 0.0
            price_quantity = 0.0
            price_discount_amount = 0.0

        # Line level.
        if (
            line_extension_amount
            and not invoiced_quantity
        ):
            price_unit = subtotal
            quantity = 1.0
            discount_amount = total_allowances

            # Combine with the price level. Suppose:
            # line_extension_amount = 1000.0
            # price_subtotal = 1250.0
            # price_quantity = 5.0
            # price_discount_amount = 250.0
            # In that case, we want to compute:
            # price_unit = 250.0
            # quantity = 5.0
            # discount_amount = 250.0
            if not currency.is_zero(price_subtotal):
                quantity = subtotal * price_quantity / (price_subtotal - price_discount_amount)
                price_unit = (subtotal / quantity) + (price_discount_amount / price_quantity)
                discount_amount += price_discount_amount * quantity / price_quantity

        elif (
            line_extension_amount
            and invoiced_quantity
        ):
            quantity = invoiced_quantity
            price_unit = subtotal / quantity
            discount_amount = total_allowances

            # Combine with the price level. Suppose:
            # line_extension_amount = 1200.0
            # quantity = 6
            # price_subtotal = 1250.0
            # price_quantity = 5.0
            # price_discount_amount = 50.0
            # In that case, we want to compute:
            # price_unit = 250.0
            # quantity = 6.0
            # discount_amount = 300.0
            if not currency.is_zero(price_subtotal):
                price_unit = price_subtotal / price_quantity
                discount_amount += price_discount_amount * quantity / price_quantity
        else:
            quantity = 0.0
            price_unit = 0.0
            discount_amount = total_allowances

            # Combine with the price level.
            if not currency.is_zero(price_subtotal):
                price_unit = price_subtotal / price_quantity
                quantity = price_quantity
                discount_amount += price_discount_amount

        # Extra charges.
        price_unit += total_charges / (quantity or 1.0)

        # Turn discount_amount to a percentage
        gross_subtotal = price_unit * quantity
        discount = (discount_amount * 100 / gross_subtotal) if gross_subtotal else 0.0

        to_write = collected_values['to_write']
        to_write['quantity'] = quantity
        to_write['price_unit'] = price_unit
        to_write['discount'] = discount