def _compute_recurrence(self):
        recurrence_fields = self._get_recurrent_fields()
        false_values = {field: False for field in recurrence_fields}  # computes need to set a value
        defaults = self.env['calendar.recurrence'].default_get(recurrence_fields)
        default_rrule_values = self.recurrence_id.default_get(recurrence_fields)
        for event in self:
            if event.recurrency:
                current_rrule = (event.rrule_type if event.rrule_type_ui == "custom" else event.rrule_type_ui)
                event.update(defaults)  # default recurrence values are needed to correctly compute the recurrence params
                event_values = event._get_recurrence_params()
                rrule_values = {
                    field: event.recurrence_id[field]
                    for field in recurrence_fields
                    if event.recurrence_id[field]
                }
                rrule_values = rrule_values or default_rrule_values
                rrule_values['rrule_type'] = current_rrule or rrule_values.get('rrule_type') or defaults['rrule_type']
                event.update({**false_values, **defaults, **event_values, **rrule_values})
            else:
                event.update(false_values)