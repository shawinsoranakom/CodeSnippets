def stop(self, stage):
        """stop tracking for the passed stage"""

        # deal with nested calls of eval during train - simply ignore those
        if self.cur_stage is not None and self.cur_stage != stage:
            return

        # this sends a signal to peak_monitor_func to complete its loop
        self.peak_monitoring = False

        # first ensure all objects get collected and their memory is freed
        gc.collect()

        if self.torch is not None:
            if torch.cuda.is_available():
                self.torch.cuda.empty_cache()
            elif is_torch_mlu_available():
                self.torch.mlu.empty_cache()
            elif is_torch_musa_available():
                self.torch.musa.empty_cache()
            elif is_torch_xpu_available():
                self.torch.xpu.empty_cache()
            elif is_torch_npu_available():
                self.torch.npu.empty_cache()
            elif is_torch_hpu_available():
                # not available on hpu as it reserves all device memory for the current process
                # self.torch.npu.empty_cache()
                pass
            elif is_torch_mps_available():
                self.torch.mps.empty_cache()

        # concepts:
        # - alloc_delta:  the difference of allocated memory between the end and the start
        # - peaked_delta: the difference between the peak memory and the current memory
        # in order to know how much memory the measured code consumed one needs to sum these two

        # gpu
        if self.torch is not None:
            if torch.cuda.is_available():
                self.gpu_mem_used_now = self.torch.cuda.memory_allocated()
                self.gpu_mem_used_peak = self.torch.cuda.max_memory_allocated()
            elif is_torch_mlu_available():
                self.gpu_mem_used_now = self.torch.mlu.memory_allocated()
                self.gpu_mem_used_peak = self.torch.mlu.max_memory_allocated()
            elif is_torch_musa_available():
                self.gpu_mem_used_now = self.torch.musa.memory_allocated()
                self.gpu_mem_used_peak = self.torch.musa.max_memory_allocated()
            elif is_torch_xpu_available():
                self.gpu_mem_used_now = self.torch.xpu.memory_allocated()
                self.gpu_mem_used_peak = self.torch.xpu.max_memory_allocated()
            elif is_torch_npu_available():
                self.gpu_mem_used_now = self.torch.npu.memory_allocated()
                self.gpu_mem_used_peak = self.torch.npu.max_memory_allocated()
            elif is_torch_hpu_available():
                self.gpu_mem_used_now = self.torch.hpu.memory_allocated()
                self.gpu_mem_used_peak = self.torch.hpu.max_memory_allocated()
            elif is_torch_mps_available():
                self.gpu_mem_used_now = self.torch.mps.current_allocated_memory()
                # self.torch.mps.max_memory_allocated() does not exist yet
                self.gpu_mem_used_peak = None

            else:
                raise ValueError("No available GPU device found!")

            self.gpu[self.cur_stage] = {
                "begin": self.gpu_mem_used_at_start,
                "end": self.gpu_mem_used_now,
                "alloc": (self.gpu_mem_used_now - self.gpu_mem_used_at_start),
            }
            if self.gpu_mem_used_peak is not None:
                self.gpu[self.cur_stage]["peaked"] = max(0, self.gpu_mem_used_peak - self.gpu_mem_used_now)
            else:
                self.gpu[self.cur_stage]["peaked"] = "Not available"

        # cpu
        self.cpu_mem_used_now = self.cpu_mem_used()
        self.cpu[self.cur_stage] = {
            "begin": self.cpu_mem_used_at_start,
            "end": self.cpu_mem_used_now,
            "alloc": (self.cpu_mem_used_now - self.cpu_mem_used_at_start),
            "peaked": max(0, self.cpu_mem_used_peak - self.cpu_mem_used_now),
        }

        # reset - cycle finished
        self.cur_stage = None