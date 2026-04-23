async def test_kv_producer_heterogeneous_tp(monkeypatch, d_tp_size):
    """
    Tests heterogeneous TP support in the producer transfer path.

    Verifies correct pointer and offset calculation when producer TP=2
    sends to consumer with TP=1 (P>D) or TP=4 (P<D).

    Parametrized cases:
    - P TP=2 > D TP=1: one D rank receives; dst_offset based on P rank
    - P TP=2 < D TP=4: two D ranks receive; src_offset based on D rank
    """

    P_TP_SIZE = 2
    P_TP_RANK = 0
    LOCAL_BLOCK_LEN = 4096

    local_block_len = LOCAL_BLOCK_LEN
    remote_block_len = LOCAL_BLOCK_LEN * P_TP_SIZE // d_tp_size

    monkeypatch.setenv("VLLM_MOONCAKE_ABORT_REQUEST_TIMEOUT", "5")
    vllm_config = create_vllm_config(
        kv_connector="MooncakeConnector", kv_role="kv_producer"
    )

    with set_current_vllm_config(vllm_config), patch_worker_dependencies():
        prefill_connector = MooncakeConnector(vllm_config, KVConnectorRole.WORKER)
        prefill_worker = prefill_connector.connector_worker

        # Override TP rank/size to simulate P TP=2
        prefill_worker.tp_rank = P_TP_RANK
        prefill_worker.tp_size = P_TP_SIZE
        prefill_worker._tp_size[prefill_worker.engine_id] = P_TP_SIZE
        prefill_worker.transfer_topo.tp_rank = P_TP_RANK
        prefill_worker.transfer_topo.tp_size = P_TP_SIZE

        prefill_worker.kv_caches_base_addr = [0x1000]
        prefill_worker.block_len_per_layer = [local_block_len]

        origin_sender_loop = prefill_worker.sender_loop
        prefill_worker.sender_loop = asyncio.get_event_loop()

        transfer_id = "xfer-hetero-1"
        local_block_ids = [10, 11]
        send_meta = SendBlockMeta(
            p_req_id="p-req-h1",
            transfer_id=transfer_id,
            local_block_ids=local_block_ids,
            ready=asyncio.Event(),
        )
        prefill_worker.reqs_need_send[transfer_id] = send_meta
        send_meta.ready.set()

        # Compute target D ranks using the production code path
        target_d_ranks = prefill_worker.transfer_topo.handshake_target_ranks(d_tp_size)

        mock_socket = AsyncMock(spec=zmq.asyncio.Socket)
        mock_socket.send_multipart = AsyncMock()
        identity = b"consumer-hetero"

        # Assign different remote block IDs per D rank
        d_rank_remote_blocks = {
            rank: [20 + i * 10, 21 + i * 10] for i, rank in enumerate(target_d_ranks)
        }

        with patch.object(
            prefill_worker, "_send_blocks", return_value=0
        ) as mock_send_blocks:
            for d_rank in target_d_ranks:
                remote_block_ids = d_rank_remote_blocks[d_rank]
                xfer_meta = MooncakeXferMetadata(
                    remote_hostname="consumer-host",
                    remote_port=54321,
                    remote_tp_size=d_tp_size,
                    remote_tp_rank=d_rank,
                    req_blocks={
                        f"d-req-h1-r{d_rank}": (
                            transfer_id,
                            remote_block_ids,
                        )
                    },
                    kv_caches_base_addr=[0x2000],
                    block_lens=[remote_block_len],
                )

                mock_send_blocks.reset_mock()
                mock_socket.send_multipart.reset_mock()

                await prefill_worker.send_kv_to_decode(identity, mock_socket, xfer_meta)

                # Verify _send_blocks was called
                mock_send_blocks.assert_called_once()
                call_args = mock_send_blocks.call_args[0]
                src_ptrs = call_args[1]
                dst_ptrs = call_args[2]
                lengths = call_args[3]

                # Heterogeneous TP: blocks cannot be coalesced because
                # local and remote block_lens differ
                assert len(src_ptrs) == len(local_block_ids)
                assert len(dst_ptrs) == len(local_block_ids)
                assert len(lengths) == len(local_block_ids)

                # Compute expected offsets based on TP ratio
                if d_tp_size <= P_TP_SIZE:
                    tp_ratio = P_TP_SIZE // d_tp_size
                    expected_src_off = 0
                    expected_dst_off = (P_TP_RANK % tp_ratio) * local_block_len
                    expected_xfer_len = local_block_len
                else:
                    ratio_abs = d_tp_size // P_TP_SIZE
                    expected_src_off = (d_rank % ratio_abs) * remote_block_len
                    expected_dst_off = 0
                    expected_xfer_len = remote_block_len

                for idx, (lblk, rblk) in enumerate(
                    zip(local_block_ids, remote_block_ids)
                ):
                    assert src_ptrs[idx] == (
                        0x1000 + lblk * local_block_len + expected_src_off
                    )
                    assert dst_ptrs[idx] == (
                        0x2000 + rblk * remote_block_len + expected_dst_off
                    )
                    assert lengths[idx] == expected_xfer_len

                # Verify successful response sent back to consumer
                mock_socket.send_multipart.assert_called_once()
                _, sent_payload = mock_socket.send_multipart.call_args[0][0]
                response = prefill_worker._xfer_resp_decoder.decode(sent_payload)
                assert response.status == MooncakeXferResponseStatus.FINISH
                assert response.ok_reqs == [f"d-req-h1-r{d_rank}"]

        # After serving all D ranks, the request should be complete
        assert transfer_id not in prefill_worker.reqs_need_send
        assert "p-req-h1" in prefill_worker.finished_sending_reqs

        prefill_worker.sender_loop = origin_sender_loop
        prefill_worker.shutdown()