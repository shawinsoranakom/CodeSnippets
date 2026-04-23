def train_batch(modeldef):
        # CUDA events for timing
        if device == "cuda":
            timer_class = torch.cuda.Event
        else:
            timer_class = Event

        fwd_start_event = timer_class(enable_timing=True)
        fwd_end_event = timer_class(enable_timing=True)
        bwd_start_event = timer_class(enable_timing=True)
        bwd_end_event = timer_class(enable_timing=True)

        gc.collect()

        fwd_start_event.record()
        with record_function("## forward ##"):
            forward_output = modeldef.forward(*modeldef.inputs)
        fwd_end_event.record()

        # XXX: Use if need to print something
        # print(modeldef.forward.graph_for(*modeldef.inputs))

        if modeldef.backward_setup is not None:
            backward_input = modeldef.backward_setup(forward_output)
        else:
            backward_input = forward_output

        gc.collect()

        bwd_start_event.record()
        if modeldef.backward is not None:
            modeldef.backward(*backward_input)
        bwd_end_event.record()

        if modeldef.backward is not None:
            with torch.no_grad():
                for param in modeldef.params:
                    if param.grad is None:
                        raise AssertionError("Parameter gradient must not be None")
                    param.grad.zero_()

        if device == "cuda":
            torch.cuda.synchronize()

        fwd_time = fwd_start_event.elapsed_time(fwd_end_event)
        bwd_time = bwd_start_event.elapsed_time(bwd_end_event)
        return fwd_time, bwd_time