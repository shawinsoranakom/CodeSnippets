def _compute_display_name(self):
        super()._compute_display_name()
        with_remaining_hours = self.env.context.get('with_remaining_hours') and not self.env.context.get('skip_remaining_hours', False)
        if with_remaining_hours and any(line.remaining_hours_available for line in self):
            company = self.env.company
            encoding_uom = company.timesheet_encode_uom_id
            is_hour = is_day = False
            unit_label = ''
            if encoding_uom == self.env.ref('uom.product_uom_hour'):
                is_hour = True
                unit_label = _('remaining')
            elif encoding_uom == self.env.ref('uom.product_uom_day'):
                is_day = True
                unit_label = _('days remaining')
            for line in self:
                if line.remaining_hours_available:
                    remaining_time = ''
                    if is_hour:
                        remaining_time = f' ({format_duration(line.remaining_hours)} {unit_label})'
                    elif is_day:
                        remaining_days = company.project_time_mode_id._compute_quantity(line.remaining_hours, encoding_uom, round=False)
                        remaining_time = f' ({remaining_days:.02f} {unit_label})'
                    name = f'{line.display_name}{remaining_time}'
                    line.display_name = name