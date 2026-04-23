def _set_duration(self):

        def _float_duration_to_second(duration):
            minutes = duration // 1
            seconds = (duration % 1) * 60
            return minutes * 60 + seconds

        for order in self:
            old_order_duration = order.get_duration()
            new_order_duration = order.duration
            if new_order_duration == old_order_duration:
                continue

            delta_duration = new_order_duration - old_order_duration

            if delta_duration > 0:
                if order.state not in ('progress', 'done', 'cancel'):
                    order.state = 'progress'
                enddate = fields.Datetime.now()
                date_start = enddate - timedelta(seconds=_float_duration_to_second(delta_duration))
                if order.duration_expected >= new_order_duration or old_order_duration >= order.duration_expected:
                    # either only productive or only performance (i.e. reduced speed) time respectively
                    self.env['mrp.workcenter.productivity'].create(
                        order._prepare_timeline_vals(new_order_duration, date_start, enddate)
                    )
                else:
                    # split between productive and performance (i.e. reduced speed) times
                    maxdate = fields.Datetime.from_string(enddate) - relativedelta(minutes=new_order_duration - order.duration_expected)
                    self.env['mrp.workcenter.productivity'].create([
                        order._prepare_timeline_vals(order.duration_expected, date_start, maxdate),
                        order._prepare_timeline_vals(new_order_duration, maxdate, enddate)
                    ])
            else:
                duration_to_remove = abs(delta_duration)
                timelines_to_unlink = self.env['mrp.workcenter.productivity']
                for timeline in order.time_ids.sorted():
                    if duration_to_remove <= 0.0:
                        break
                    if timeline.duration <= duration_to_remove:
                        duration_to_remove -= timeline.duration
                        timelines_to_unlink |= timeline
                    else:
                        new_time_line_duration = timeline.duration - duration_to_remove
                        timeline.date_start = timeline.date_end - timedelta(seconds=_float_duration_to_second(new_time_line_duration))
                        break
                timelines_to_unlink.unlink()