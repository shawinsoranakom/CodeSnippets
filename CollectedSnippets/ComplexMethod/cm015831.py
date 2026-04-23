def validate_choices(choices):
            if max_autotune:
                if len(choices) <= 2:
                    raise AssertionError(
                        f"Max-autotune should have >2 choices, got {len(choices)}"
                    )
                if not any(isinstance(c, ExternKernelCaller) for c in choices):
                    raise AssertionError("Should have ExternKernelCaller")
                if not any(isinstance(c, TritonTemplateCaller) for c in choices):
                    raise AssertionError("Should have TritonTemplateCaller")
            else:
                if len(choices) != 1:
                    raise AssertionError(
                        f"No max-autotune should have 1 choice, got {len(choices)}"
                    )
                if not isinstance(choices[0], ExternKernelCaller):
                    raise AssertionError(
                        f"Should be ExternKernelCaller, got {type(choices[0])}"
                    )
            return choices