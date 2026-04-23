def find_nodes_prefer_channels_last(self) -> OrderedSet[Node]:
        """
        The rule to decide if an node prefer channels last is simple.
        1. if it's input/output of a convolution
        2. if one of its user prefers channels last

        We have rule 1 because cudnn runs a faster convolution kernel for channels last inputs;
        Rule 2 is also important. It makes sure that indirect inputs to convolution also prefers
        channels last.

        Consider the scenario: conv -> batch-norm -> relu -> conv
        Without rule 2, batch-norm output may use a contiguous layout. That will cause 2 extra copies:
        1. the output of batch-norm should be channels last initially since its input is a conv's output.
           Forcing the batch-norm's output to be contiguous results in the first copy
        2. The second conv's input is initially contiguous. This layout is propagated from the batch-norm's output.
           We need convert it to channels last layout which results in the second copy.
        With rule 2, we makes sure all the tensors in the chain uses channels last layout. So both copies
        can be saved.
        """
        last_conv = None
        nodes_cannot_propagate = [torch.ops.aten.bmm.default]
        output_set = OrderedSet[Node]()
        for n in reversed(self.module.graph.nodes):  # type: ignore[arg-type, union-attr]
            if n.target is torch.ops.aten.convolution.default:
                output_set.add(n)
                if last_conv is None:
                    last_conv = n
                continue
            if n.target in nodes_cannot_propagate:
                continue
            if is_mkldnn_conv(n):
                output_set.add(n)
                continue
            for user in n.users:
                if user in output_set:
                    output_set.add(n)
                    break

        # need a second pass to add downstream nodes of those channel last nodes to the sets.
        # This pass is especially needed to avoid mix-layout kernel inputs in backward pass.
        #
        # Let's say a conv-batchnorm 's output is passed to relu whose output is in turn returned
        # from the fwd graph. Without this second pass, we will force relu's output to be contiguous.
        # Then in the kernel in backward pass, the contiguous output of relu may be mix with other channels last
        # tensors and passed to a kernel.
        #
        # This pass improve yolov3 training speedup from 1.116x (worse than disabling layout optimization speedup 1.196x) to 1.457x.
        # It also improves dla102 training speedup from 1.240x (worse than disabling layout optimization speedup 1.523x) to 1.835x .
        # This also helps the following models:
        # - res2net101_26w_4s
        # - res2net50_14w_8s
        # - sebotnet33ts_256
        for n in self.module.graph.nodes:  # type: ignore[union-attr]
            # layout propagation ends at last conv node, which will benefit vison transformers.
            if last_conv is not None and n == last_conv:
                break
            if n in output_set:
                for user in n.users:
                    if user.target in nodes_cannot_propagate:
                        continue
                    output_set.add(user)

        return output_set