def _output_data(self) -> None:
        """
        output the data.
        """
        self._metadata.start_at = getTsNow()
        self.log_json(self._metadata.to_json())

        while not self.exit_event.is_set():
            collecting_start_time = time.time()
            stats = UtilizationRecord(
                level="record",
                timestamp=getTsNow(),
            )

            try:
                data_list, error_list, log_list = self.shared_resource.get_and_reset()
                if self._debug_mode:
                    print(
                        f"collected data: {len(data_list)}, errors found: {len(error_list)}, logs {len(log_list)}"
                    )
                # records and clears found errors
                errors = list(set(error_list))

                # if has errors but data list is None, a bug may exist in the monitor code, log the errors
                if not data_list and len(errors) > 0:
                    raise ValueError(
                        f"no data is collected but detected errors during the interval: {errors}, logs: {log_list}"
                    )
                if not data_list:
                    # pass since no data is collected
                    continue

                cpu_stats = self._generate_stats(
                    [data.cpu_percent for data in data_list]
                )
                memory_stats = self._generate_stats(
                    [data.memory_percent for data in data_list]
                )

                # find all cmds during the interval
                cmds = {
                    process["cmd"] for data in data_list for process in data.processes
                }

                stats.cmd_names = list(cmds)
                record = RecordData()
                record.cpu = cpu_stats
                record.memory = memory_stats

                # collect gpu metrics
                if self._has_pynvml or self._has_amdsmi:
                    gpu_list = self._calculate_gpu_utilization(data_list)
                    record.gpu_usage = gpu_list
                stats.data = record
                stats.logs = log_list
            except Exception as e:
                stats = UtilizationRecord(
                    level="record", timestamp=getTsNow(), error=str(e)
                )
            finally:
                collecting_end_time = time.time()
                time_diff = collecting_end_time - collecting_start_time
                # verify there is data
                if stats.level:
                    stats.log_duration = f"{time_diff * 1000:.2f} ms"
                    self.log_json(stats.to_json())
                time.sleep(self._log_interval)
        # shut down gpu connections when exiting
        self._shutdown_gpu_connections()