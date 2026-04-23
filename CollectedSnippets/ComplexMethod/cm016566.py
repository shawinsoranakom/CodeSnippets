def get_hooks_for_clip_schedule(self):
        scheduled_hooks: dict[WeightHook, list[tuple[tuple[float,float], HookKeyframe]]] = {}
        # only care about WeightHooks, for now
        for hook in self.get_type(EnumHookType.Weight):
            hook: WeightHook
            hook_schedule = []
            # if no hook keyframes, assign default value
            if len(hook.hook_keyframe.keyframes) == 0:
                hook_schedule.append(((0.0, 1.0), None))
                scheduled_hooks[hook] = hook_schedule
                continue
            # find ranges of values
            prev_keyframe = hook.hook_keyframe.keyframes[0]
            for keyframe in hook.hook_keyframe.keyframes:
                if keyframe.start_percent > prev_keyframe.start_percent and not math.isclose(keyframe.strength, prev_keyframe.strength):
                    hook_schedule.append(((prev_keyframe.start_percent, keyframe.start_percent), prev_keyframe))
                    prev_keyframe = keyframe
                elif keyframe.start_percent == prev_keyframe.start_percent:
                    prev_keyframe = keyframe
            # create final range, assuming last start_percent was not 1.0
            if not math.isclose(prev_keyframe.start_percent, 1.0):
                hook_schedule.append(((prev_keyframe.start_percent, 1.0), prev_keyframe))
            scheduled_hooks[hook] = hook_schedule
        # hooks should not have their schedules in a list of tuples
        all_ranges: list[tuple[float, float]] = []
        for range_kfs in scheduled_hooks.values():
            for t_range, keyframe in range_kfs:
                all_ranges.append(t_range)
        # turn list of ranges into boundaries
        boundaries_set = set(itertools.chain.from_iterable(all_ranges))
        boundaries_set.add(0.0)
        boundaries = sorted(boundaries_set)
        real_ranges = [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)]
        # with real ranges defined, give appropriate hooks w/ keyframes for each range
        scheduled_keyframes: list[tuple[tuple[float,float], list[tuple[WeightHook, HookKeyframe]]]] = []
        for t_range in real_ranges:
            hooks_schedule = []
            for hook, val in scheduled_hooks.items():
                keyframe = None
                # check if is a keyframe that works for the current t_range
                for stored_range, stored_kf in val:
                    # if stored start is less than current end, then fits - give it assigned keyframe
                    if stored_range[0] < t_range[1] and stored_range[1] > t_range[0]:
                        keyframe = stored_kf
                        break
                hooks_schedule.append((hook, keyframe))
            scheduled_keyframes.append((t_range, hooks_schedule))
        return scheduled_keyframes