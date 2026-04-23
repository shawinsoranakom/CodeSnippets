def rank_events(self, length):
        """
        Filter and Rank the events based on some heuristics:
        1) Events that are in the falling phase of the queue depth.
        2) Events that have a high idle_time, self_time difference.

        Parameters:
            length: The number of events to return.
        """

        # Find the interval when qd is falling to 0
        import torch

        queue_depth_list = list(reversed(self.queue_depth_list))
        qd_values = [e.queue_depth for e in queue_depth_list]

        bottom_threashold = 0
        top_threashold = 4
        decrease_interval = []
        i = 0
        while i < len(qd_values):
            if qd_values[i] > bottom_threashold:
                i += 1
                continue
            for j in range(i + 1, len(qd_values)):
                # Find next zero and if the max value between them exceeds
                # the threshold, then we have a falling interval
                next_minimum_idx = index_of_first_match(
                    qd_values, lambda x: x <= bottom_threashold, start=j
                )
                peak_idx = argmax(qd_values, start=j, end=next_minimum_idx)

                # if is a valid peak, we add to list and continue
                if peak_idx is not None and qd_values[peak_idx] >= top_threashold:
                    decrease_interval.append(
                        Interval(
                            queue_depth_list[peak_idx].start, queue_depth_list[i].start
                        )
                    )
                    i = next_minimum_idx if next_minimum_idx is not None else i
                    break
            i += 1
        # Filter out events that are not in the decrease interval
        event_list = [
            event
            for event in self.metrics
            if event.intervals_overlap(decrease_interval)
        ]
        if event_list:
            self_time = torch.tensor(
                [self.metrics[event].self_time_ns for event in event_list],
                dtype=torch.float32,
            )
            idle_time = torch.tensor(
                [self.metrics[event].fraction_idle_time for event in event_list],
                dtype=torch.float32,
            )
            normalized_gain = (idle_time - torch.mean(idle_time)) / torch.std(idle_time)
            normalized_self = (self_time - torch.mean(self_time)) / torch.std(self_time)
            heuristic_score_list = normalized_gain + 0.6 * normalized_self

            # Sort events by heuristic
            event_list = [
                event
                for _, event in sorted(
                    zip(heuristic_score_list, event_list, strict=True),
                    key=operator.itemgetter(0),
                    reverse=True,
                )
            ]
            event_list = event_list[:length]
        return event_list