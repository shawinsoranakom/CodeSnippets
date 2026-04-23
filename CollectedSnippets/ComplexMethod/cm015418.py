def _call_collective_with_varying_tensors(self, backend, collective, *args):
        # call collective with varying tensors to ensure that the tensors are
        # correctly dispatched

        # TODO: this will be updated in the future to not be backend specific
        device = "cuda" if backend == "nccl" else "xpu" if backend == "xccl" else "cpu"
        # ensure supported devices (cpu, cuda) succeeds during dispatch call
        tensor = torch.zeros(2, 2, device=torch.device(device))
        # multi tensor collectives
        if collective is dist.barrier:
            collective()
        elif collective in (dist.all_gather, dist.gather):
            collective([tensor], tensor, *args)
        elif collective is dist.scatter:
            collective(tensor, [tensor], *args)
        elif collective in (dist.reduce_scatter, dist.all_to_all):
            # gloo does not support reduce_scatter or all_to_all
            if backend != "gloo":
                if collective is dist.reduce_scatter:
                    collective(tensor, [tensor], *args)
                else:
                    collective([tensor], [tensor], *args)
        else:
            collective(tensor, *args)