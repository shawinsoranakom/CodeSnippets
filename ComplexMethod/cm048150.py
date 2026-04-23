def _range_calculation(self, event, duration):
        """ Calculate the range of recurrence when applying the recurrence
        The following issues are taken into account:
            start of period is sometimes in the past (weekly or monthly rule).
            We can easily filter these range values but then the count value may be wrong...
            In that case, we just increase the count value, recompute the ranges and dismiss the useless values
        """
        self.ensure_one()
        original_count = self.end_type == 'count' and self.count
        ranges = set(self._get_ranges(event.start, duration))
        future_events = set((x, y) for x, y in ranges if x.date() >= event.start.date() and y.date() >= event.start.date())
        if original_count and len(future_events) < original_count:
            # Rise count number because some past values will be dismissed.
            self.count = (2*original_count) - len(future_events)
            ranges = set(self._get_ranges(event.start, duration))
            # We set back the occurrence number to its original value
            self.count = original_count
        # Remove ranges of events occurring in the past
        ranges = set((x, y) for x, y in ranges if x.date() >= event.start.date() and y.date() >= event.start.date())
        return ranges