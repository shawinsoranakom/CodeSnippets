def _maybe_produce_instance(self, instance: api.Value) -> None:
        instance_data = self._instances[instance]
        while instance_data.pending:
            entry = instance_data.pending[0]
            if (
                self._time_finished is None
                or entry.time > self._time_finished
                or entry not in instance_data.finished
            ):
                break
            if instance_data.buffer_time != entry.time:
                assert (
                    instance_data.buffer_time is None
                    or instance_data.buffer_time < entry.time
                )
                self._flush_buffer(instance_data)
                instance_data.buffer_time = entry.time
            result = instance_data.finished.pop(entry)
            if result == _AsyncStatus.FAILURE:
                instance_data.correct = False
            instance_data.buffer.append(
                (entry.key, entry.is_addition, entry.task_id, result)
            )
            instance_data.pending.popleft()

        if (
            not instance_data.pending
            or instance_data.pending[0].time != instance_data.buffer_time
        ):  # if (instance, processing_time) pair is finished
            self._flush_buffer(instance_data)
        if not instance_data.pending:
            del self._instances[instance]