def _compute_combo_price(self, parent_line):
        """
        This method is a python version of odoo/addons/point_of_sale/static/src/app/models/utils/compute_combo_items.js
        It is used to compute the price of combo items on the server side when an order is received from
        the POS frontend. In an accounting perspective, isn't correct but we still waiting the combo
        computation from accounting side.
        """
        child_lines = parent_line.combo_line_ids
        currency = parent_line.order_id.currency_id
        taxes = self.fiscal_position_id.map_tax(parent_line.product_id.taxes_id)
        parent_line.tax_ids = taxes
        parent_lst_price = self.pricelist_id._get_product_price(parent_line.product_id, parent_line.qty)
        child_line_free = []
        child_line_extra = []

        child_lines_by_combo = {}
        for line in child_lines:
            combo = line.combo_item_id.combo_id
            child_lines_by_combo.setdefault(combo, []).append(line)

        for combo, child_lines in child_lines_by_combo.items():
            free_count = 0
            max_free = combo.qty_free

            for line in child_lines:
                qty_free = max(0, max_free - free_count)
                free_qty = min(line.qty, qty_free)
                extra_qty = line.qty - free_qty

                if free_qty > 0:
                    child_line_free.append(line)
                    free_count += free_qty

                if extra_qty > 0:
                    child_line_extra.append(line)

        original_total = sum(line.combo_item_id.combo_id.base_price * line.qty for line in child_line_free if line.combo_item_id.combo_id.qty_free > 0)
        remaining_total = parent_lst_price

        for index, child in enumerate(child_line_free):
            combo_item = child.combo_item_id
            combo = combo_item.combo_id
            unit_devision_factor = original_total or 1
            price_unit = currency.round(combo.base_price * parent_lst_price / unit_devision_factor)
            remaining_total -= price_unit * child.qty

            if index == len(child_line_free) - 1:
                price_unit += remaining_total
                remaining_total = 0

            selected_attributes = child.attribute_value_ids
            price_extra = sum(attr.price_extra for attr in selected_attributes)
            total_price = price_unit + price_extra + child.combo_item_id.extra_price
            child.price_unit = total_price

        extra_original_total = 0
        if remaining_total and child_line_extra:
            extra_original_total = sum(
                line.combo_item_id.combo_id.base_price * line.qty
                for line in child_line_extra
            ) or 1

        for index, child in enumerate(child_line_extra):
            combo_item = child.combo_item_id
            price_unit = currency.round(combo_item.combo_id.base_price)

            if extra_original_total:
                remaining_proportion = currency.round(
                    combo_item.combo_id.base_price * parent_lst_price / extra_original_total
                )
                price_unit += remaining_proportion
                remaining_total -= remaining_proportion * child.qty

                if index == len(child_line_extra) - 1:
                    price_unit += remaining_total / child.qty

            selected_attributes = child.attribute_value_ids
            price_extra = sum(attr.price_extra for attr in selected_attributes)
            total_price = price_unit + price_extra + child.combo_item_id.extra_price
            child.price_unit = total_price