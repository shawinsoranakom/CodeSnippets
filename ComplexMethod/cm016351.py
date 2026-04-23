def _initial_gpu_handler(self) -> None:
        """
        Initializes the GPU handlers if gpus are available, and updates the log summary info.
        """
        try:
            if self._has_pynvml:
                self._gpu_lib_detected = "pynvml"
                # Todo: investigate if we can use device uuid instead of index.
                # there is chance that the gpu index can change when the gpu is rebooted.
                self._gpu_handles = [
                    pynvml.nvmlDeviceGetHandleByIndex(i)
                    for i in range(pynvml.nvmlDeviceGetCount())
                ]
            if self._has_amdsmi:
                self._gpu_lib_detected = "amdsmi"
                self._gpu_handles = amdsmi.amdsmi_get_processor_handles()

            self._num_of_cpus = psutil.cpu_count(logical=True)
            # update summary info
            self._metadata.gpu_count = len(self._gpu_handles)
            self._metadata.cpu_count = self._num_of_cpus

            if self._has_pynvml or self._has_amdsmi:
                if len(self._gpu_handles) == 0:
                    self._metadata.gpu_type = ""
                else:
                    self._metadata.gpu_type = self._gpu_lib_detected
        except Exception as e:
            self._metadata.error = str(e)