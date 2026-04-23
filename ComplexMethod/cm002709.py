def start(self):
        """start tracking for the caller's stage"""
        if self.skip_memory_metrics:
            return

        stage = self.derive_stage()
        # deal with nested calls of eval during train - simply ignore those
        if self.cur_stage is not None and self.cur_stage != stage:
            return

        self.cur_stage = stage

        gc.collect()

        if self.torch is not None:
            if torch.cuda.is_available():
                self.torch.cuda.reset_peak_memory_stats()
                self.torch.cuda.empty_cache()
            elif is_torch_mlu_available():
                self.torch.mlu.reset_peak_memory_stats()
                self.torch.mlu.empty_cache()
            elif is_torch_musa_available():
                self.torch.musa.reset_peak_memory_stats()
                self.torch.musa.empty_cache()
            elif is_torch_xpu_available():
                self.torch.xpu.reset_peak_memory_stats()
                self.torch.xpu.empty_cache()
            elif is_torch_npu_available():
                self.torch.npu.reset_peak_memory_stats()
                self.torch.npu.empty_cache()
            elif is_torch_hpu_available():
                self.torch.hpu.reset_peak_memory_stats()
                # not available on hpu as it reserves all device memory for the current process
                # self.torch.hpu.empty_cache()
            elif is_torch_mps_available():
                self.torch.mps.empty_cache()

        # gpu
        if self.torch is not None:
            if torch.cuda.is_available():
                self.gpu_mem_used_at_start = self.torch.cuda.memory_allocated()
            elif is_torch_mlu_available():
                self.gpu_mem_used_at_start = self.torch.mlu.memory_allocated()
            elif is_torch_musa_available():
                self.gpu_mem_used_at_start = self.torch.musa.memory_allocated()
            elif is_torch_xpu_available():
                self.gpu_mem_used_at_start = self.torch.xpu.memory_allocated()
            elif is_torch_npu_available():
                self.gpu_mem_used_at_start = self.torch.npu.memory_allocated()
            elif is_torch_hpu_available():
                self.gpu_mem_used_at_start = self.torch.hpu.memory_allocated()
            elif is_torch_mps_available():
                self.gpu_mem_used_at_start = self.torch.mps.current_allocated_memory()

        # cpu
        self.cpu_mem_used_at_start = self.cpu_mem_used()

        self.peak_monitoring = True
        peak_monitor_thread = threading.Thread(target=self.peak_monitor_func)
        peak_monitor_thread.daemon = True
        peak_monitor_thread.start()