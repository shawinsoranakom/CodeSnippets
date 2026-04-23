def _monitor_worker(gpu_type: str, sample_interval_sec: float, connection: Connection):
        """Worker process for GPU monitoring."""
        gpu_utilization = []
        gpu_memory_used = []
        timestamps = []
        device_handle = None

        # Initialize GPU-specific monitoring
        if gpu_type == "amd":
            amdsmi.amdsmi_init()
            device_handle = amdsmi.amdsmi_get_processor_handles()[0]
        elif gpu_type == "nvidia":
            pynvml.nvmlInit()
            device_handle = pynvml.nvmlDeviceGetHandleByIndex(0)

        # Signal ready
        try:
            connection.send(0)
        except Exception:
            return

        # Monitoring loop
        stop = False
        while not stop:
            try:
                if gpu_type == "amd":
                    utilization, memory_used = get_amd_gpu_stats(device_handle)
                elif gpu_type == "nvidia":
                    utilization, memory_used = get_nvidia_gpu_stats(device_handle)
                elif gpu_type == "intel":
                    utilization, memory_used = get_intel_xpu_stats()
                else:
                    break

                gpu_utilization.append(utilization)
                gpu_memory_used.append(memory_used)
                timestamps.append(time.time())
            except Exception as e:
                # Skips failed measurements
                _logger.debug(f"Failed to collect GPU metrics sample: {e}")

            stop = connection.poll(sample_interval_sec)

        # Cleanup
        if gpu_type == "amd":
            try:
                amdsmi.amdsmi_shut_down()
            except Exception as e:
                _logger.debug(f"Failed to shutdown AMD GPU monitoring: {e}")
        elif gpu_type == "nvidia":
            try:
                pynvml.nvmlShutdown()
            except Exception as e:
                _logger.debug(f"Failed to shutdown NVIDIA GPU monitoring: {e}")

        # Send results back
        try:
            connection.send((gpu_utilization, gpu_memory_used, timestamps))
        except Exception as e:
            _logger.error(f"Failed to send GPU monitoring results: {e}")

        connection.close()