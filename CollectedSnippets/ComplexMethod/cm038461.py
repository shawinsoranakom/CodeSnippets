def _nixl_handshake(
        self,
        host: str,
        port: int,
        remote_tp_size: int,
        expected_engine_id: str,
    ) -> dict[int, str]:
        """Do a NIXL handshake with a remote instance."""

        # the first time we connect to a remote agent.
        # be careful, the handshake happens in a background thread.
        # it does not have an active cuda context until any cuda runtime
        # call is made. when UCX fails to find a valid cuda context, it will
        # disable any cuda ipc communication, essentially disabling any NVLink
        # communication.
        # when we are using device buffers, we need to set the device
        # explicitly to make sure the handshake background thread has a valid
        # cuda context.
        if not self.use_host_buffer:
            current_platform.set_device(self.device_id)

        # When target instance TP > local TP, we need to perform multiple
        # handshakes. Do it in a single background job for simplicity.
        # Regardless, only handshake with the remote TP rank(s) that current
        # local rank will read from. Note that With homogeneous TP,
        # this happens to be the same single rank_i.
        assert self.transfer_topo is not None
        p_remote_ranks = self.transfer_topo.handshake_target_ranks(remote_tp_size)
        remote_rank_to_agent_name = {}
        path = make_zmq_path("tcp", host, port)

        with zmq_ctx(zmq.REQ, path) as sock:
            for remote_rank in p_remote_ranks:
                logger.debug(
                    "Querying metadata on path: %s at remote tp rank %s",
                    path,
                    remote_rank,
                )

                start_time = time.perf_counter()
                # Send query for the request.
                msg = msgspec.msgpack.encode((GET_META_MSG, remote_rank))
                # Set receive timeout to 5 seconds to avoid hanging on dead server
                sock.setsockopt(zmq.RCVTIMEO, 5000)  # milliseconds
                sock.send(msg)
                handshake_bytes = sock.recv()

                # Decode handshake payload to get compatibility hash
                handshake_decoder = msgspec.msgpack.Decoder(NixlHandshakePayload)
                try:
                    handshake_payload = handshake_decoder.decode(handshake_bytes)
                except (msgspec.DecodeError, msgspec.ValidationError) as e:
                    raise RuntimeError(
                        f"Failed to decode NixlHandshakePayload. This likely indicates "
                        f"an incompatibility between connector version. Error: {e}"
                    ) from e

                got_metadata_time = time.perf_counter()
                logger.debug(
                    "NIXL handshake: get metadata took: %s",
                    got_metadata_time - start_time,
                )

                # Check compatibility hash BEFORE decoding agent metadata
                assert self.compat_hash is not None
                if (
                    self.enforce_compat_hash
                    and handshake_payload.compatibility_hash != self.compat_hash
                ):
                    raise RuntimeError(
                        f"NIXL compatibility hash mismatch. "
                        f"Local: {self.compat_hash}, "
                        f"Remote: {handshake_payload.compatibility_hash}. "
                        f"Prefill and decode instances have incompatible "
                        f"configurations. This may be due to: different vLLM versions,"
                        f" models, dtypes, KV cache layouts, attention backends, etc. "
                        f"Both instances must use identical configurations."
                        f"Disable this check using "
                        f'--kv-transfer-config \'{{"kv_connector_extra_config": '
                        f'{{"enforce_handshake_compat": false}}}}\''
                    )

                logger.info(
                    "NIXL compatibility check passed (hash: %s)",
                    handshake_payload.compatibility_hash,
                )

                # Decode agent metadata
                metadata_decoder = msgspec.msgpack.Decoder(NixlAgentMetadata)
                try:
                    metadata = metadata_decoder.decode(
                        handshake_payload.agent_metadata_bytes
                    )
                except (msgspec.DecodeError, msgspec.ValidationError) as e:
                    # This should not happen if hash matched
                    raise RuntimeError(
                        f"Failed to decode NixlAgentMetadata. Error: {e}"
                    ) from e

                # Ensure engine id matches.
                if metadata.engine_id != expected_engine_id:
                    raise RuntimeError(
                        f"Remote NIXL agent engine ID mismatch. "
                        f"Expected {expected_engine_id},"
                        f"received {metadata.engine_id}."
                    )

                # Register Remote agent.
                remote_agent_name = self.add_remote_agent(
                    metadata, remote_rank, remote_tp_size
                )
                setup_agent_time = time.perf_counter()
                logger.debug(
                    "NIXL handshake: add agent took: %s",
                    setup_agent_time - got_metadata_time,
                )
                remote_rank_to_agent_name[remote_rank] = remote_agent_name
        return remote_rank_to_agent_name