async def test_kv_producer(monkeypatch):
    """
    Simulates a Producer Worker (Prefiller) receiving a transfer request
    from a Consumer (Decoder).

    Verifies memory offset calculation: ptr = base_addr + block_id * block_len.
    """

    monkeypatch.setenv("VLLM_MOONCAKE_ABORT_REQUEST_TIMEOUT", "5")
    vllm_config = create_vllm_config(
        kv_connector="MooncakeConnector", kv_role="kv_producer"
    )

    with set_current_vllm_config(vllm_config), patch_worker_dependencies():
        prefill_connector = MooncakeConnector(vllm_config, KVConnectorRole.WORKER)
        prefill_worker = prefill_connector.connector_worker
        prefill_worker.kv_caches_base_addr = [0x1000]
        block_len = 4096
        prefill_worker.block_len_per_layer = [block_len]

        # Override loop to use current test loop
        origin_sender_loop = prefill_worker.sender_loop
        prefill_worker.sender_loop = asyncio.get_event_loop()

        # A request is finished on Producer and ready to be sent.
        transfer_id = "xfer-req-1"
        send_meta = SendBlockMeta(
            p_req_id="p-req-1",
            transfer_id=transfer_id,
            local_block_ids=[10, 11],
            ready=asyncio.Event(),
        )
        prefill_worker.reqs_need_send[transfer_id] = send_meta
        send_meta.ready.set()

        # Remote consumer request metadata
        xfer_meta = MooncakeXferMetadata(
            remote_hostname="consumer-host",
            remote_port=54321,
            remote_tp_size=1,
            remote_tp_rank=0,
            req_blocks={"d-req-1": (transfer_id, [20, 21])},
            kv_caches_base_addr=[0x2000],
            block_lens=[block_len],
        )

        mock_socket = AsyncMock(spec=zmq.asyncio.Socket)
        mock_socket.send_multipart = AsyncMock()
        identity = b"consumer-id"

        with patch.object(
            prefill_worker, "_send_blocks", return_value=0
        ) as mock_send_blocks:
            # Normal case: 2 blocks to 2 blocks
            # Worker processes the consumer's request
            await prefill_worker.send_kv_to_decode(identity, mock_socket, xfer_meta)
            # Verify transfer parameters are correct
            src_ptr = 0x1000 + 10 * block_len
            dst_ptr = 0x2000 + 20 * block_len
            length = 2 * block_len
            mock_send_blocks.assert_called_once_with(
                "consumer-host:54321", [src_ptr], [dst_ptr], [length]
            )
            mock_socket.send_multipart.assert_called_once()

            # Verify the response sent back to the consumer
            sent_call = mock_socket.send_multipart.call_args[0][0]
            sent_identity, sent_payload = sent_call
            assert sent_identity == identity
            response = prefill_worker._xfer_resp_decoder.decode(sent_payload)
            assert response.status == MooncakeXferResponseStatus.FINISH
            assert response.ok_reqs == ["d-req-1"]

            # Verify internal state cleanup
            assert transfer_id not in prefill_worker.reqs_need_send
            assert "p-req-1" in prefill_worker.finished_sending_reqs

            # More cases:
            # Consumer only needs 1 block (less than P)
            mock_send_blocks.reset_mock()
            mock_socket.send_multipart.reset_mock()
            prefill_worker.reqs_need_send[transfer_id] = send_meta
            send_meta.sent = 0
            send_meta.ready.set()
            xfer_meta.req_blocks["d-req-1"] = (transfer_id, [20])
            # Worker processes the consumer's request
            await prefill_worker.send_kv_to_decode(identity, mock_socket, xfer_meta)
            # Verify transfer parameters are correct: 11 to 20
            src_ptr = 0x1000 + 11 * block_len
            dst_ptr = 0x2000 + 20 * block_len
            length = 1 * block_len
            mock_send_blocks.assert_called_once_with(
                "consumer-host:54321", [src_ptr], [dst_ptr], [length]
            )
            mock_socket.send_multipart.assert_called_once()

            # Consumer needs 3 blocks (more than P, error case)
            mock_send_blocks.reset_mock()
            mock_socket.send_multipart.reset_mock()
            prefill_worker.reqs_need_send[transfer_id] = send_meta
            send_meta.sent = 0
            send_meta.ready.set()
            xfer_meta.req_blocks["d-req-1"] = (transfer_id, [20, 21, 22])
            # Worker processes the consumer's request
            await prefill_worker.send_kv_to_decode(identity, mock_socket, xfer_meta)
            # This should not be called because error.
            mock_send_blocks.assert_not_called()
            mock_socket.send_multipart.assert_called_once()
            _, sent_payload = mock_socket.send_multipart.call_args[0][0]
            response = prefill_worker._xfer_resp_decoder.decode(sent_payload)
            assert response.err_msg == "P num blocks less than D"
            assert response.err_reqs == ["d-req-1"]

            # Timeout
            mock_send_blocks.reset_mock()
            mock_socket.send_multipart.reset_mock()
            prefill_worker.reqs_need_send[transfer_id] = send_meta
            send_meta.sent = 0
            send_meta.ready.clear()
            xfer_meta.req_blocks["d-req-1"] = (transfer_id, [20, 21])
            # Worker processes the consumer's request
            await prefill_worker.send_kv_to_decode(identity, mock_socket, xfer_meta)
            # This should not be called because timeout.
            mock_send_blocks.assert_not_called()
            mock_socket.send_multipart.assert_called_once()
            _, sent_payload = mock_socket.send_multipart.call_args[0][0]
            response = prefill_worker._xfer_resp_decoder.decode(sent_payload)
            assert response.err_msg == "Timeout waiting for P side ready."
            assert response.err_reqs == ["d-req-1"]

        # Transfer error
        with patch.object(
            prefill_worker, "_send_blocks", return_value=123
        ) as mock_send_blocks:
            mock_socket.send_multipart.reset_mock()
            prefill_worker.reqs_need_send[transfer_id] = send_meta
            send_meta.sent = 0
            send_meta.ready.set()
            xfer_meta.req_blocks["d-req-1"] = (transfer_id, [20, 21])
            # Worker processes the consumer's request
            await prefill_worker.send_kv_to_decode(identity, mock_socket, xfer_meta)
            mock_send_blocks.assert_called_once()
            mock_socket.send_multipart.assert_called_once()
            _, sent_payload = mock_socket.send_multipart.call_args[0][0]
            response = prefill_worker._xfer_resp_decoder.decode(sent_payload)
            assert response.err_msg == "Mooncake transfer engine returned 123"
            assert response.err_reqs == ["d-req-1"]

        # Clean up
        prefill_worker.sender_loop = origin_sender_loop
        prefill_worker.shutdown()