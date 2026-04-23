def get_mutated_args_sub_kernels(self) -> list[str]:
        mutated_args: OrderedSet[str] = OrderedSet()
        for sub_kernel in self.sub_kernels:
            for mutation in sub_kernel.mutations:
                if mutation in sub_kernel.args.input_buffers:
                    mutated_args.add(sub_kernel.args.input_buffers[mutation])
                if (
                    mutation in sub_kernel.args.inplace_buffers
                    and mutation not in V.graph.removed_buffers
                    and mutation not in sub_kernel.removed_buffers
                ):
                    mutated_args.add(
                        cast(
                            InplacedBuffer, sub_kernel.args.inplace_buffers[mutation]
                        ).inner_name
                    )
                if mutation in sub_kernel.args.output_buffers:
                    arg = sub_kernel.args.output_buffers[mutation]
                    assert not isinstance(arg, RemovedArg)
                    mutated_args.add(arg)
        return sorted(mutated_args)