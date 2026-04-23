def _simulate_operation_planning(self, operation, product, start_date, quantity, planning_per_operation=False, simulated_leaves_per_workcenter=False):
        """ Simulate planning of an operation depending on its workcenter/alternatives work schedule.
        (see '_plan_workorder')
        """
        operation.ensure_one()
        if planning_per_operation is False:
            planning_per_operation = {}
        if simulated_leaves_per_workcenter is False:
            simulated_leaves_per_workcenter = defaultdict(list)
        # Plan operation after its predecessors
        date_start = max(start_date, datetime.now())
        for op in operation.blocked_by_operation_ids:
            if op._skip_operation_line(product):
                continue
            if op not in planning_per_operation:
                self._simulate_operation_planning(op, product, start_date, quantity, planning_per_operation, simulated_leaves_per_workcenter)
            date_start = max(date_start, planning_per_operation[op]['date_finished'])
        # Consider workcenter and alternatives
        workcenters = operation.workcenter_id | operation.workcenter_id.alternative_workcenter_ids
        best_date_finished = datetime.max
        best_date_start = best_workcenter = best_duration_expected = None
        for workcenter in workcenters:
            if not workcenter.resource_calendar_id:
                raise UserError(_('There is no defined calendar on workcenter %s.', workcenter.name))
            # Compute theoretical duration
            duration_expected = operation.with_context(product=product, quantity=quantity, workcenter=workcenter).time_total
            # Try to plan on workcenter
            from_date, to_date = workcenter._get_first_available_slot(date_start, duration_expected, extra_leaves_slots=simulated_leaves_per_workcenter[workcenter])
            # If the workcenter is unavailable, try planning on the next one
            if not from_date:
                continue
            # Check if this workcenter is better than the previous ones
            if to_date and to_date < best_date_finished:
                best_date_start = from_date
                best_date_finished = to_date
                best_workcenter = workcenter
                best_duration_expected = duration_expected
        # If none of the workcenter are available, raise
        if best_date_finished == datetime.max:
            raise UserError(_('Impossible to plan. Please check the workcenter availabilities.'))
        planning_per_operation[operation] = {
            'date_start': best_date_start,
            'date_finished': best_date_finished,
            'workcenter': best_workcenter,
            'duration_expected': best_duration_expected,
        }
        simulated_leaves_per_workcenter[best_workcenter].append((best_date_start, best_date_finished))
        return planning_per_operation