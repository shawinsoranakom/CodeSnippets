def test_compute_date_finished_with_workcenter_calendar(self):
        """
        Test that finished date of the production depends properly on the workcenter availability.

        Have two wokcenters: WC1 (op 1) opened 8/5, WC2 opened 24/5 (op 2, 3)

        Check finish date for a production of:
            - 1 unit
            - 10 units (exceeds one day of work for WC1)
        """
        calendars = self.env['resource.calendar'].sudo().create([
            {
                'attendance_ids': [
                    Command.create({
                        'dayofweek': str(weekday),
                        'day_period': period,
                        'hour_from': am_start if period == 'morning' else pm_start,
                        'hour_to': am_end if period == 'morning' else pm_end,
                        'name': f'Day {weekday} {period} H {f"{am_start} {am_end}" if period == "morning" else f"{pm_start} {pm_end}"}',
                    })
                    for weekday in range(5)
                    for period in ('morning', 'afternoon')
                ],
                'leave_ids': [Command.create({
                    'date_from': datetime(2024, 1, 8, 0, 0, 0),
                    'date_to': datetime(2024, 1, 9, 0, 0, 0),
                })],
                'name': name,
                'tz': 'UTC',
            }
            for am_start, am_end, pm_start, pm_end, name in [
                (8, 12, 13, 17, 'Test calendar 40h'),
                (0, 12, 12, 24, 'Test full calendar 24h/5d')
            ]
        ])
        workcenters = self.env['mrp.workcenter'].create([
            {
                'name': f'Simple Workcenter {i}',
                'time_start': 0,
                'time_stop': 0,
                'time_efficiency': time_efficiency,
                'resource_calendar_id': calendars[i].id,
            }
            for i, time_efficiency in enumerate([50, 100])
        ])
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_6.product_tmpl_id.id,
            'product_qty': 1.0,
            'operation_ids': [
                Command.create({'name': 'Op 1', 'workcenter_id': workcenters[0].id,
                        'time_mode_batch': 1, 'time_mode': "auto", 'time_cycle_manual': 18}),
                Command.create({'name': 'Op 2', 'workcenter_id': workcenters[1].id,
                        'time_mode_batch': 1, 'time_mode': "auto", 'time_cycle_manual': 24}),
                Command.create({'name': 'Op 3', 'workcenter_id': workcenters[1].id,
                        'time_mode_batch': 1, 'time_mode': "auto", 'time_cycle_manual': 66}),
            ],
            'type': 'normal',
            'bom_line_ids': [
                Command.create({'product_id': self.product_1.id, 'product_qty': 1}),
            ],
        })
        production = self.env['mrp.production'].create(
            {
                'product_id': self.product_6.id,
                'bom_id': bom.id,
                'product_qty': 1,
                'date_start': datetime(2024, 1, 1, 8, 0, 0),
            },
        )
        production.action_confirm()
        self.assertAlmostEqual(production.date_finished, datetime(2024, 1, 1, 9, 30, 0), delta=timedelta(seconds=2))

        production.write({'date_start': datetime(2024, 1, 1, 10, 0, 0), 'product_qty': 10})
        # First WC finished on the first day, the second one still has 1 hour to do
        self.assertAlmostEqual(production.date_finished, datetime(2024, 1, 2, 1, 0, 0), delta=timedelta(seconds=2))

        production.write({'date_start': datetime(2024, 1, 1, 16, 0, 0)})
        # Start at 16pm, so still 5h to do the next day
        self.assertAlmostEqual(production.date_finished, datetime(2024, 1, 2, 14, 0, 0), delta=timedelta(seconds=2))

        production.write({'date_start': datetime(2024, 1, 5, 16, 0, 0)})
        # The workcenter does not work in the weekend + the monday is a leave
        self.assertAlmostEqual(production.date_finished, datetime(2024, 1, 9, 14, 0, 0), delta=timedelta(seconds=2))