def __init__(self, skip_memory_metrics=False):
        self.skip_memory_metrics = skip_memory_metrics

        if not is_psutil_available():
            # soft dependency on psutil
            self.skip_memory_metrics = True

        if self.skip_memory_metrics:
            return

        import psutil

        if is_torch_cuda_available() or is_torch_mlu_available() or is_torch_musa_available():
            import torch

            self.torch = torch
            self.gpu = {}
        elif is_torch_mps_available():
            import torch

            self.torch = torch
            self.gpu = {}
        elif is_torch_xpu_available():
            import torch

            self.torch = torch
            self.gpu = {}
        elif is_torch_npu_available():
            import torch

            self.torch = torch
            self.gpu = {}
        elif is_torch_hpu_available():
            import torch

            self.torch = torch
            self.gpu = {}
        else:
            self.torch = None

        self.process = psutil.Process()

        self.cur_stage = None
        self.cpu = {}
        self.init_reported = False