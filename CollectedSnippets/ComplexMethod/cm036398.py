def check_handshake(remote_tp_size: int):
            tp_ratio = remote_tp_size // local_tp_size
            assert set(remote_agents.keys()) == set(range(tp_ratio))

            remote_engine_id = worker.REMOTE_ENGINE_ID
            remote_info = worker.transfer_topo.get_engine_info(remote_engine_id)
            assert remote_info.remote_tp_size == remote_tp_size
            assert -tp_ratio == worker.transfer_topo.tp_ratio(remote_tp_size)
            # ensure src_xfer_handles_by_tp_ratio is populated with tpratio chunks
            assert -tp_ratio in worker.src_xfer_handles_by_tp_ratio
            assert len(worker.src_xfer_handles_by_tp_ratio[-tp_ratio]) == tp_ratio
            assert remote_engine_id in worker.dst_xfer_side_handles
            assert set(worker.dst_xfer_side_handles[remote_engine_id].keys()) == set(
                range(tp_ratio)
            )