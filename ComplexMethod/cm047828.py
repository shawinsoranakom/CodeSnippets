def _get_duration_expected(self, alternative_workcenter=False, ratio=1):
        self.ensure_one()
        if not self.workcenter_id:
            return self.duration_expected
        capacity, setup, cleanup = self.workcenter_id._get_capacity(self.product_id, self.product_uom_id, self.production_bom_id.product_qty or 1)
        if not self.operation_id:
            duration_expected_working = (self.duration_expected - setup - cleanup) * self.workcenter_id.time_efficiency / 100.0
            if duration_expected_working < 0:
                duration_expected_working = 0
            if self.qty_producing not in (0, self.qty_production, self._origin.qty_producing):
                qty_ratio = self.qty_producing / (self._origin.qty_producing or self.qty_production)
            else:
                qty_ratio = 1
            return setup + cleanup + duration_expected_working * qty_ratio * ratio * 100.0 / self.workcenter_id.time_efficiency
        qty_production = self.qty_producing or self.qty_production
        cycle_number = float_round(qty_production / capacity, precision_digits=0, rounding_method='UP')
        if alternative_workcenter:
            # TODO : find a better alternative : the settings of workcenter can change
            duration_expected_working = (self.duration_expected - setup - cleanup) * self.workcenter_id.time_efficiency / (100.0 * cycle_number)
            if duration_expected_working < 0:
                duration_expected_working = 0
            capacity, setup, cleanup = alternative_workcenter._get_capacity(self.product_id, self.product_uom_id, self.production_bom_id.product_qty or 1)
            cycle_number = float_round(qty_production / capacity, precision_digits=0, rounding_method='UP')
            return setup + cleanup + cycle_number * duration_expected_working * 100.0 / alternative_workcenter.time_efficiency
        time_cycle = self.operation_id.time_cycle
        return setup + cleanup + cycle_number * time_cycle * 100.0 / self.workcenter_id.time_efficiency