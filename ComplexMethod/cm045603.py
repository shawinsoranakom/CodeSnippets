async def loop_forever(event_loop: asyncio.AbstractEventLoop):
            self._maybe_create_queue()

            while True:
                request = await self._requests.get()
                if request == "*FINISH*":
                    break
                if isinstance(request, int):  # time end
                    self._on_time_end(request)
                    continue

                (key, values, time, diff) = request
                row = {}
                input_table = self._transformer._input_table
                task_id = values[-1]
                values = values[:-1]
                if input_table is not None:
                    for field_name, field_value in zip(
                        input_table._columns.keys(), values, strict=True
                    ):
                        row[field_name] = field_value
                else:
                    for i, field_value in enumerate(values):
                        row[f"{i}"] = field_value

                assert diff in [-1, 1], "diff should be 1 or -1"
                addition = diff == 1
                instance = row.get(_INSTANCE_COLUMN, key)
                entry = _Entry(
                    key=key, time=time, is_addition=addition, task_id=task_id
                )
                self._instances[instance].pending.append(entry)

                previous_task = self._tasks.get(key, None)

                async def task(
                    key: Pointer,
                    values: dict[str, Any],
                    time: int,
                    addition: bool,
                    task_id: Pointer,
                    previous_task: asyncio.Task | None,
                ):
                    instance = values.pop(_INSTANCE_COLUMN, key)
                    if not addition:
                        if previous_task is not None:
                            await previous_task
                        self._on_task_finished(
                            key,
                            instance,
                            time,
                            is_addition=False,
                            result=None,
                            task_id=task_id,
                        )
                    else:
                        result: dict[str, Any] | _AsyncStatus
                        try:
                            result = await self._invoke(**values)
                            self._check_result_against_schema(result)
                        except Exception:
                            self._logger.error(
                                "Exception in AsyncTransformer:", exc_info=True
                            )
                            result = _AsyncStatus.FAILURE
                        # If there is a task pending for this key,
                        # let's wait for it and discard result to preserve order
                        # for this key (the instance may change)
                        if previous_task is not None:
                            await previous_task
                        self._on_task_finished(
                            key,
                            instance,
                            time,
                            is_addition=True,
                            result=result,
                            task_id=task_id,
                        )

                current_task = event_loop.create_task(
                    task(key, row, time, addition, task_id, previous_task)
                )
                self._tasks[key] = current_task

            await asyncio.gather(*self._tasks.values())