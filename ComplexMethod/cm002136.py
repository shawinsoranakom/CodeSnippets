def stop_and_collect(self) -> GPURawMetrics:
        """Stop monitoring and return collected metrics."""
        # No GPU available or unsupported GPU
        if self.process is None:
            return GPURawMetrics(
                utilization=[],
                memory_used=[],
                timestamps=[],
                timestamp_0=0.0,
                monitoring_status=GPUMonitoringStatus.NO_GPUS_AVAILABLE,
            )

        # Process crashed before we could collect results
        process_failed = False
        if not self.process.is_alive():
            process_failed = True
            gpu_utilization, gpu_memory_used, timestamps = [], [], []
        else:
            # Signal stop
            self.parent_connection.send(0)
            # Get results
            try:
                gpu_utilization, gpu_memory_used, timestamps = self.parent_connection.recv()
            except Exception:
                process_failed = True
                gpu_utilization, gpu_memory_used, timestamps = [], [], []

        self.parent_connection.close()
        self.process.join(timeout=2.0)
        if self.process.is_alive():
            self.process.terminate()

        if gpu_utilization:
            timestamp_0 = timestamps[0]
            metrics = GPURawMetrics(
                utilization=gpu_utilization,
                memory_used=gpu_memory_used,
                timestamps=[t - timestamp_0 for t in timestamps],
                timestamp_0=timestamp_0,
                monitoring_status=GPUMonitoringStatus.SUCCESS,
            )
            self.logger.debug(f"GPU monitoring completed: {len(gpu_utilization)} samples collected")
        elif process_failed:
            metrics = GPURawMetrics(
                utilization=[],
                memory_used=[],
                timestamps=[],
                timestamp_0=0.0,
                monitoring_status=GPUMonitoringStatus.FAILED,
            )
            self.logger.warning("GPU monitoring failed (process crashed or timed out)")
        else:
            metrics = GPURawMetrics(
                utilization=[],
                memory_used=[],
                timestamps=[],
                timestamp_0=0.0,
                monitoring_status=GPUMonitoringStatus.NO_SAMPLES_COLLECTED,
            )
        return metrics