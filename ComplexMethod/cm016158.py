def check_accuracy(self, args, kwargs) -> None:
        res = {}
        for backend in self.available_backends:
            args_ref, kwargs_ref = self.clone_inputs(args, kwargs)
            res[backend] = getattr(self, backend)(args_ref, kwargs_ref)()

        if (
            "compiled" in self.available_backends
            and self.script_args.custom_compile_options
        ):
            torch._dynamo.reset()  # cause recompile
            with torch._inductor.config.patch(self.script_args.custom_compile_options):
                args_ref, kwargs_ref = self.clone_inputs(args, kwargs)
                res[self.script_args.custom_compile_name] = self.compiled(
                    args_ref, kwargs_ref
                )()

        gold = res["eager"]

        tol = {}
        if self.script_args.tolerance:
            tol = {
                "atol": self.script_args.tolerance,
                "rtol": self.script_args.tolerance,
            }
        for backend in res:
            if backend == "eager":
                continue
            try:
                torch.testing.assert_close(res[backend], gold, **tol)
                for t, gold_t in zip(res[backend], gold):
                    if t.requires_grad:
                        torch.testing.assert_close(t.grad, gold_t.grad, **tol)
                print(
                    f"Accuracy check \033[92m✓ succeed\033[0m for {backend} backend on {self.name} kernel"
                )
            except Exception as e:
                print(
                    f"Accuracy check \033[91m✗ failed\033[0m for {backend} backend on {self.name} kernel. Error {e}"
                )
                if self.script_args.exit_on_accuracy_failure:
                    print("Exit right away since --exit-on-accuracy-failure is set")
                    sys.exit(1)