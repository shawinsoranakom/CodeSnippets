def run_impl(self, use_fuser):
        warmups = 10
        if self.device == "cuda":
            iters = 1000
        else:
            iters = 10
        engine = tensor_engine.get_engine()

        self.bm_jit = None
        for i in range(warmups + iters):
            if i == warmups:
                if self.device == "cuda":
                    engine.sync_cuda()
                time_start = time.time()

            if i == 0:
                if self.jit_mode == "trace" and use_fuser:
                    self.bm_jit = torch.jit.trace(
                        self.forward, example_inputs=self.inputs, check_trace=False
                    )
                if callable(getattr(self, "reference", None)):
                    self.check()
                else:
                    print("Warning: no reference result for ", self.module())
            elif i == 1:
                # The fusion graph is visible after the first iter is executed
                if self.jit_mode == "trace" and use_fuser and self.print_ir:
                    print(self.bm_jit.graph_for(*self.inputs))
            z = self.compute()
            if self.mode == "both":
                if self.result_grad is None:
                    self.result_grad = engine.rand_like(z)
                engine.backward([z], [self.result_grad], self.grad_variables)

        if self.device == "cuda":
            engine.sync_cuda()

        duration = time.time() - time_start
        iter_time = duration / iters
        memory_workload = self.memory_workload()
        compute_workload = self.compute_workload()

        result_dict = {
            "desc": self.desc(),
            "us": iter_time * 1e6,
            "sol": memory_workload["sol"] * self.dtype_to_bytes() / iter_time / 1e9,
            "algorithmic": memory_workload["algorithmic"]
            * self.dtype_to_bytes()
            / iter_time
            / 1e9,
        }
        if compute_workload:
            result_dict["compute_workload"] = compute_workload / iter_time / 1e9
        self.dump_result(result_dict)