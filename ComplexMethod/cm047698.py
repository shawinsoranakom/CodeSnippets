def process(self, entries, continuous=True, hide_gaps=False, use_context=True, constant_time=False, aggregate_sql=False, **params):
        # constant_time parameters is mainly useful to hide temporality when focussing on sql determinism
        entry_end = previous_end = None
        if not entries:
            return []
        events = []
        current_stack_ids = []
        frames_start = entries[0]['start']

        # add last closing entry if missing
        last_entry = entries[-1]
        if last_entry['stack']:
            entries.append({'stack': [], 'start': last_entry['start'] + last_entry.get('time', 0)})

        for index, entry in enumerate(entries):
            if constant_time:
                entry_start = close_time = index
            else:
                previous_end = entry_end
                if hide_gaps and previous_end:
                    entry_start = previous_end
                else:
                    entry_start = entry['start'] - frames_start

                if previous_end and previous_end > entry_start:
                    # skip entry if entry starts after another entry end
                    continue

                if previous_end:
                    close_time = min(entry_start, previous_end)
                else:
                    close_time = entry_start

                entry_time = entry.get('time')
                entry_end = None if entry_time is None else entry_start + entry_time

            entry_stack_ids = self.stack_to_ids(
                entry['stack'] or [],
                use_context and entry.get('exec_context'),
                aggregate_sql,
                self.init_stack_trace_level
            )
            level = 0
            if continuous:
                level = -1
                for current, new in zip(current_stack_ids, entry_stack_ids):
                    level += 1
                    if current != new:
                        break
                else:
                    level += 1

            for frame in reversed(current_stack_ids[level:]):
                events.append({
                    "type": "C",
                    "frame": frame,
                    "at": close_time
                })
            for frame in entry_stack_ids[level:]:
                events.append({
                    "type": "O",
                    "frame": frame,
                    "at": entry_start
                })
            current_stack_ids = entry_stack_ids

        return events