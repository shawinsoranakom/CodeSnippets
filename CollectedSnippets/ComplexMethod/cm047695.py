def add_output(self, names, complete=True, display_name=None, use_context=True, constant_time=False, context_per_name = None, **params):
        """
        Add a profile output to the list of profiles
        :param names: list of keys to combine in this output. Keys corresponds to the one used in add
        :param display_name: name of the tab for this output
        :param complete: display the complete stack. If False, don't display the stack bellow the profiler.
        :param use_context: use execution context (added by ExecutionContext context manager) to display the profile.
        :param constant_time: hide temporality. Useful to compare query counts
        :param context_per_name: a dictionary of additionnal context per name
        """
        entries = []
        display_name = display_name or ','.join(names)
        for name in names:
            raw = self.profiles_raw.get(name)
            if not raw:
                continue
            entries += raw
        entries.sort(key=lambda e: e['start'])
        result = self.process(entries, use_context=use_context, constant_time=constant_time, **params)
        if not result:
            return self
        start = result[0]['at']
        end = result[-1]['at']

        if complete:
            start_stack = []
            end_stack = []
            init_stack_trace_ids = self.stack_to_ids(self.init_stack_trace, use_context and entries[0].get('exec_context'))
            for frame_id in init_stack_trace_ids:
                start_stack.append({
                    "type": "O",
                    "frame": frame_id,
                    "at": start
                })
            for frame_id in reversed(init_stack_trace_ids):
                end_stack.append({
                    "type": "C",
                    "frame": frame_id,
                    "at": end
                })
            result = start_stack + result + end_stack

        self.profiles.append({
            "name": display_name,
            "type": "evented",
            "unit": "entries" if constant_time else "seconds",
            "startValue": 0,
            "endValue": end - start,
            "events": result
        })
        return self