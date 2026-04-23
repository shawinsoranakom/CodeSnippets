def _compute_json_popover(self):
        if self.ids:
            conflicted_dict = self._get_conflicted_workorder_ids()
        for wo in self:
            infos = []
            if not wo.date_start or not wo.date_finished or not wo.ids:
                wo.show_json_popover = False
                wo.json_popover = False
                continue
            if wo.state in ('blocked', 'ready'):
                previous_wos = wo.blocked_by_workorder_ids
                previous_starts = previous_wos.filtered('date_start').mapped('date_start')
                previous_finished = previous_wos.filtered('date_finished').mapped('date_finished')
                prev_start = min(previous_starts) if previous_starts else False
                prev_finished = max(previous_finished) if previous_finished else False
                if wo.state == 'blocked' and prev_start and not (prev_start > wo.date_start):
                    infos.append({
                        'color': 'text-primary',
                        'msg': _("Waiting the previous work order, planned from %(start)s to %(end)s",
                            start=format_datetime(self.env, prev_start, dt_format=False),
                            end=format_datetime(self.env, prev_finished, dt_format=False))
                    })
                if wo.date_finished < fields.Datetime.now():
                    infos.append({
                        'color': 'text-warning',
                        'msg': _("The work order should have already been processed.")
                    })
                if prev_start and prev_start > wo.date_start:
                    infos.append({
                        'color': 'text-danger',
                        'msg': _("Scheduled before the previous work order, planned from %(start)s to %(end)s",
                            start=format_datetime(self.env, prev_start, dt_format=False),
                            end=format_datetime(self.env, prev_finished, dt_format=False))
                    })
                if conflicted_dict.get(wo.id):
                    infos.append({
                        'color': 'text-danger',
                        'msg': _("Planned at the same time as other workorder(s) at %s", wo.workcenter_id.display_name)
                    })
            color_icon = infos and infos[-1]['color'] or False
            wo.show_json_popover = bool(color_icon)
            wo.json_popover = json.dumps({
                'popoverTemplate': 'mrp.workorderPopover',
                'infos': infos,
                'color': color_icon,
                'icon': 'fa-exclamation-triangle' if color_icon in ['text-warning', 'text-danger'] else 'fa-info-circle',
                'replan': color_icon not in [False, 'text-primary']
            })