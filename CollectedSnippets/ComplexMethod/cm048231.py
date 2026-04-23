def _compute_count_repair(self):
        repair_picking_types = self.filtered(lambda picking: picking.code == 'repair_operation')

        # By default, set count_repair_xxx to False
        self.count_repair_ready = False
        self.count_repair_confirmed = False
        self.count_repair_under_repair = False
        self.count_repair_late = False

        # shortcut
        if not repair_picking_types:
            return

        picking_types = self.env['repair.order']._read_group(
            [
                ('picking_type_id', 'in', repair_picking_types.ids),
                ('state', 'in', ('confirmed', 'under_repair')),
            ],
            groupby=['picking_type_id', 'is_parts_available', 'state'],
            aggregates=['id:count']
        )

        late_repairs = self.env['repair.order']._read_group(
            [
                ('picking_type_id', 'in', repair_picking_types.ids),
                ('state', '=', 'confirmed'),
                '|',
                ('schedule_date', '<', fields.Date.today()),
                ('is_parts_late', '=', True),
            ],
            groupby=['picking_type_id'],
            aggregates=['__count']
        )
        late_repairs = {pt.id: late_count for pt, late_count in late_repairs}

        counts = {}
        for pt in picking_types:
            pt_count = counts.setdefault(pt[0].id, {})
            # Only confirmed repairs (not "under repair" ones) are considered as ready
            if pt[1] and pt[2] == 'confirmed':
                pt_count.setdefault('ready', 0)
                pt_count['ready'] += pt[3]
            pt_count.setdefault(pt[2], 0)
            pt_count[pt[2]] += pt[3]

        for pt in repair_picking_types:
            if pt.id not in counts:
                continue
            pt.count_repair_ready = counts[pt.id].get('ready')
            pt.count_repair_confirmed = counts[pt.id].get('confirmed')
            pt.count_repair_under_repair = counts[pt.id].get('under_repair')
            pt.count_repair_late = late_repairs.get(pt.id, 0)