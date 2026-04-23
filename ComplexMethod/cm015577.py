def _get_load_balancer(
        self, lb_type: str, kwargs: dict[str, Any]
    ) -> _LoadBalancer | None:
        seq_length = kwargs["seq_length"]
        document_lengths = kwargs["document_lengths"]
        block_mask = kwargs["block_mask"]

        # generate load balancer
        if lb_type == "None":
            load_balancer = None  # no load-balance
        elif lb_type == "_HeadTailLoadBalancer":
            if not isinstance(seq_length, int):
                raise AssertionError(f"Expected int, got {type(seq_length)}")
            load_balancer = _HeadTailLoadBalancer(
                seq_length, self.world_size, torch.device(self.device_type)
            )
        elif lb_type == "_PerDocumentHeadTailLoadBalancer":
            if not isinstance(document_lengths, list):
                raise AssertionError(f"Expected list, got {type(document_lengths)}")
            load_balancer = _PerDocumentHeadTailLoadBalancer(
                document_lengths, self.world_size, torch.device(self.device_type)
            )
        elif lb_type == "_PTRRLoadBalancer":
            if not isinstance(block_mask, BlockMask):
                raise AssertionError(f"Expected BlockMask, got {type(block_mask)}")
            load_balancer = _PTRRLoadBalancer(
                block_mask,
                self.world_size,
            )
        else:
            raise ValueError(f"load_balancer type {lb_type} is not supported!")

        return load_balancer