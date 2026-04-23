def _get_stat_buttons(self):
        buttons = super()._get_stat_buttons()
        if not self.allow_timesheets or not self.env.user.has_group("hr_timesheet.group_hr_timesheet_user"):
            return buttons

        encode_uom = self.env.company.timesheet_encode_uom_id
        uom_ratio = self.env.ref('uom.product_uom_hour').factor / encode_uom.factor

        allocated = self.allocated_hours * uom_ratio
        effective = self.total_timesheet_time
        color = ""
        if allocated:
            number = f"{round(effective)} / {round(allocated)} {encode_uom.name}"
            success_rate = round(100 * effective / allocated)
            if success_rate > 100:
                number = self.env._(
                    "%(effective)s / %(allocated)s %(uom_name)s",
                    effective=round(effective),
                    allocated=round(allocated),
                    uom_name=encode_uom.name,
                )
                color = "text-danger"
            else:
                number = self.env._(
                    "%(effective)s / %(allocated)s %(uom_name)s (%(success_rate)s%%)",
                    effective=round(effective),
                    allocated=round(allocated),
                    uom_name=encode_uom.name,
                    success_rate=success_rate,
                )
                if success_rate >= 80:
                    color = "text-warning"
                else:
                    color = "text-success"
        else:
            number = self.env._(
                    "%(effective)s %(uom_name)s",
                    effective=round(effective),
                    uom_name=encode_uom.name,
                )

        buttons.append({
            "icon": f"clock-o {color}",
            "text": self.env._("Timesheets"),
            "number": number,
            "action_type": "object",
            "action": "action_project_timesheets",
            "show": True,
            "sequence": 2,
        })
        if allocated and success_rate > 100:
            buttons.append({
                "icon": f"warning {color}",
                "text": self.env._("Extra Time"),
                "number": self.env._(
                    "%(exceeding_hours)s %(uom_name)s (+%(exceeding_rate)s%%)",
                    exceeding_hours=round(effective - allocated),
                    uom_name=encode_uom.name,
                    exceeding_rate=round(100 * (effective - allocated) / allocated),
                ),
                "action_type": "object",
                "action": "action_project_timesheets",
                "show": True,
                "sequence": 3,
            })

        return buttons