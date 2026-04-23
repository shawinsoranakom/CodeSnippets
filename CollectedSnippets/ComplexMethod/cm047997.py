def _additional_name_per_id(self):
        name_per_id = super()._additional_name_per_id() if not self.env.context.get('hide_partner_ref') else {}
        if not self.env.context.get('with_price_unit'):
            return name_per_id

        sols_list = [list(sols) for dummy, sols in groupby(self, lambda sol: (sol.order_id, sol.product_id))]
        for sols in sols_list:
            if len(sols) <= 1 or not all(sol.is_service for sol in sols):
                continue
            for line in sols:
                additional_name = name_per_id.get(line.id)
                name = format_amount(self.env, line.price_unit, line.currency_id)
                if additional_name:
                    name += f' {additional_name}'
                name_per_id[line.id] = f'- {name}'

        return name_per_id