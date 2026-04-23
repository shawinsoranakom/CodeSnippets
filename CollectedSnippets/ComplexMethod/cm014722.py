def _backward_criterion(self, criterion, input, output, target, gradOutput=None, extra_args=None):
        if extra_args is None:
            extra_args = ()
        input_tuple = input if isinstance(input, tuple) else (input,)
        output_tuple = output if isinstance(output, tuple) else (output,)
        for i in input_tuple:
            if i.grad is not None:
                i.grad.data.zero_()
        args = input_tuple + (target,) + extra_args
        if gradOutput is None:
            gradOutput = torch.ones(())
        criterion(*args).backward(gradOutput.to(output_tuple[0]))
        if isinstance(input, tuple):
            return tuple(i.grad.data for i in input)
        else:
            return input.grad.data