def handle_current_stream(
            self,
            tx: "InstructionTranslator",
            *args: VariableTracker,
            **kwargs: VariableTracker,
        ) -> StreamVariable:
            from .streams import CudaStreamVariable

            if len(args) + len(kwargs) > 1 or (kwargs and "device" not in kwargs):
                unimplemented(
                    gb_type="unsupported arguments to torch.accelerator.current_stream",
                    context=f"args={args}, kwargs={kwargs}",
                    explanation="torch.accelerator.current_stream accepts one optional argument `device`",
                    hints=[
                        *graph_break_hints.USER_ERROR,
                    ],
                )
            try:
                if kwargs:
                    device = torch.device(kwargs["device"].as_python_constant())
                elif args:
                    device = torch.device(args[0].as_python_constant())
                else:
                    device = None

                stream_var = tx.symbolic_stream_state.cur_stream(device)
                if self.value is torch.cuda.current_stream and not isinstance(
                    stream_var, CudaStreamVariable
                ):
                    stream_var = CudaStreamVariable(
                        stream_var.proxy,
                        stream_var.value,
                        stream_var.user_object_index,
                        source=stream_var.source,
                    )
                return stream_var
            except Exception as e:
                unimplemented(
                    gb_type="bad device argument to torch.accelerator.current_stream",
                    context=f"args={args}, kwargs={kwargs}",
                    explanation="Expected valid string/torch.device argument ('cpu', 'cuda', etc.)",
                    hints=[*graph_break_hints.USER_ERROR],
                    from_exc=e,
                )