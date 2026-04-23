def _get_value_data(
        self,
        forced_std_price=False,
        at_date=False,
        ignore_manual_update=False,
        add_extra_value=True,
    ):
        """Returns the value and the quantity valued on the move
        In priority order:
        - Take value from accounting documents (invoices, bills)
        - Take value from quotations + landed costs
        - Take value from product cost

        Forced standard price is useful when we have to get the value
        of a move in the past with the standard price at that time.
        """
        # TODO: Make multi
        self.ensure_one()
        # It probably needs a priority order:
        # 1. take from Invoice/Bills
        # 2. from SO/PO lines
        # 3. standard_price

        valued_qty = remaining_qty = self._get_valued_qty()
        value = 0
        descriptions = []

        if not ignore_manual_update:
            manual_data = self._get_manual_value(
                remaining_qty, at_date)
            # In case of manual update we will skip extra cost
            if manual_data['quantity']:
                add_extra_value = False
            value += manual_data['value']
            remaining_qty -= manual_data['quantity']
            if manual_data.get('description'):
                descriptions.append(manual_data['description'])

        # 1. take from Invoice/Bills
        if remaining_qty:
            account_data = self._get_value_from_account_move(remaining_qty, at_date)
            value += account_data['value']
            remaining_qty -= account_data['quantity']
            if account_data.get('description'):
                descriptions.append(account_data['description'])

        if remaining_qty:
            production_data = self._get_value_from_production(remaining_qty, at_date)
            value += production_data["value"]
            remaining_qty -= production_data["quantity"]
            if production_data.get("description"):
                descriptions.append(production_data["description"])

        # 2. from SO/PO lines
        if remaining_qty:
            quotation_data = self._get_value_from_quotation(remaining_qty, at_date)
            value += quotation_data['value']
            remaining_qty -= quotation_data['quantity']
            if quotation_data.get('description'):
                descriptions.append(quotation_data['description'])

        # 3. from returns
        if remaining_qty:
            return_data = self._get_value_from_returns(remaining_qty, at_date)
            value += return_data['value']
            remaining_qty -= return_data['quantity']
            if return_data.get('description'):
                descriptions.append(return_data['description'])

        # 4. standard_price
        if remaining_qty:
            std_price_data = self._get_value_from_std_price(remaining_qty, forced_std_price, at_date)
            value += std_price_data['value']
            descriptions.append(std_price_data.get('description'))

        if add_extra_value:
            extra_data = self._get_value_from_extra(valued_qty, at_date)
            value += extra_data['value']
            if extra_data.get('description'):
                descriptions.append(extra_data['description'])

        return {
            'value': value,
            'quantity': valued_qty,
            'description': '\n'.join(descriptions),
        }