def _invert_intervals(intervals, first_start, last_stop):
            # Redefintion of the method to return an interval
            items = []
            prev_stop = first_start
            if not intervals:
                return Intervals([(first_start, last_stop, self.env['resource.calendar'])])
            for start, stop, record in sorted(intervals):
                if prev_stop and prev_stop < start and (float_compare((last_stop - start).total_seconds(), 0, precision_digits=1) >= 0):
                    items.append((prev_stop, start, record))
                prev_stop = max(prev_stop, stop)
            if last_stop and prev_stop < last_stop:
                items.append((prev_stop, last_stop, record))
            return Intervals(items, keep_distinct=True)