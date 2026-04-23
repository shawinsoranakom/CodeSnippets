def stack_to_ids(self, stack, context, aggregate_sql=False, stack_offset=0):
        """
            :param stack: A list of hashable frame
            :param context: an iterable of (level, value) ordered by level
            :param stack_offset: offset level for stack

            Assemble stack and context and return a list of ids representing
            this stack, adding each corresponding context at the corresponding
            level.
        """
        stack_ids = []
        context_iterator = iter(context or ())
        context_level, context_value = next(context_iterator, (None, None))
        # consume iterator until we are over stack_offset
        while context_level is not None and context_level < stack_offset:
            context_level, context_value = next(context_iterator, (None, None))
        for level, frame in enumerate(stack, start=stack_offset + 1):
            if aggregate_sql:
                frame = (frame[0], '', frame[2])
            while context_level == level:
                context_frame = (", ".join(f"{k}={v}" for k, v in context_value.items()), '', '')
                stack_ids.append(self.get_frame_id(context_frame))
                context_level, context_value = next(context_iterator, (None, None))
            stack_ids.append(self.get_frame_id(frame))
        return stack_ids