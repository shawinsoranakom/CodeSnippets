def _nixl_handshake(
        self, host: str, port: int, remote_tp_size: int, expected_engine_id: str
    ) -> dict[int, str]:
        # Mimic slow _nixl_handshake, as well as bypass zmq communication.
        time.sleep(self._hand_shake_latency)
        # These should've been done in register_kv_caches(), called by
        # gpu_model_runner. Here we just hardcode some dummy values.
        slot_size_bytes = 4096
        self.slot_size_per_layer = [slot_size_bytes]
        self.block_len_per_layer = [slot_size_bytes * self.block_size]
        self.num_blocks = 1
        self.dst_num_blocks[self.engine_id] = self.num_blocks

        assert expected_engine_id == self.REMOTE_ENGINE_ID

        # Adjust remote block length metadata to satisfy heterogeneous TP
        # invariants enforced during handshake validation.
        remote_block_lens = list(self.block_len_per_layer)
        tp_ratio = self.transfer_topo.tp_ratio(remote_tp_size)
        if remote_tp_size > self.world_size:
            # P TP > D TP case, block_len of remote is smaller
            remote_block_lens = [
                block_len // (-tp_ratio) for block_len in remote_block_lens
            ]
        elif remote_tp_size < self.world_size:
            remote_block_lens = [
                block_len * tp_ratio for block_len in remote_block_lens
            ]

        # When remote tp_size > local tp_size, handshake with multiple
        # remote ranks.
        num_handshakes = 1 if tp_ratio > 0 else -tp_ratio
        remote_agents: dict[int, str] = {}
        for remote_tp_rank in range(num_handshakes):
            remote_agent_name = self.add_remote_agent(
                NixlAgentMetadata(
                    engine_id=self.REMOTE_ENGINE_ID,
                    agent_metadata=FakeNixlWrapper.AGENT_METADATA,
                    kv_caches_base_addr=[0],
                    device_id=remote_tp_rank,
                    num_blocks=1,
                    block_lens=remote_block_lens,
                    # `self.kv_cache_layout` is only forced to HND when vllm engine
                    # is started. We mock HND here.
                    kv_cache_layout="HND",
                    block_size=self.block_size,
                    ssm_sizes=(0, 0),
                    attn_backend_name=self.backend_name,
                ),
                remote_tp_rank=remote_tp_rank,
                remote_tp_size=remote_tp_size,
            )
            remote_agents[remote_tp_rank] = remote_agent_name
        return remote_agents