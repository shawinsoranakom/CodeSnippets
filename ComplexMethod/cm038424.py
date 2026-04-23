def execute(self) -> None:
        xfer_handles: list[int] = []
        try:
            # Phase 1: pack send buffers.
            with torch.cuda.stream(self._cuda_stream):
                for dst in range(self._world_size):
                    byte_offset = dst * self._peer_partition_bytes
                    for dtype in self._dtypes:
                        peer_tensors = self._send_tensors.get(
                            dtype, [[] for _ in range(self._world_size)]
                        )[dst]
                        actual_bytes = sum(
                            t.numel() * t.element_size() for t in peer_tensors
                        )
                        if actual_bytes > self._dtype_max_bytes[dtype]:
                            raise RuntimeError(
                                "NIXL EPLB send overflow for dtype "
                                f"{dtype}: peer={dst}, "
                                f"required={actual_bytes}, "
                                f"capacity={self._dtype_max_bytes[dtype]}"
                            )
                        byte_offset = self._pack_send_buffer(
                            peer_tensors,
                            self._send_buffer,
                            byte_offset,
                        )

            # Ensure all packed data is visible in device memory before pulls.
            if self._cuda_stream is not None:
                self._cuda_stream.synchronize()
            else:
                torch.cuda.current_stream().synchronize()
            # READ is receiver-initiated; synchronize all ranks before transfer.
            # We use monitored_barrier so a rank that crashes or exits early
            # produces a diagnostic timeout instead of a silent hang.
            torch.distributed.monitored_barrier(
                group=self._cpu_group,
                timeout=timedelta(minutes=5),
            )

            # Phase 2: look up or create descriptors and issue all READs.
            # Data from all peers is packed sequentially into the single
            # partition-sized recv buffer at running offsets.
            recv_offsets: dict[int, int] = {}
            recv_offset = 0
            for src in range(self._world_size):
                if src == self._rank:
                    continue
                actual_total_bytes = 0
                for dtype in self._dtypes:
                    peer_tensors = self._recv_tensors.get(
                        dtype, [[] for _ in range(self._world_size)]
                    )[src]
                    actual_total_bytes += sum(
                        t.numel() * t.element_size() for t in peer_tensors
                    )
                if actual_total_bytes == 0:
                    continue

                recv_offsets[src] = recv_offset
                xfer_handle = self._get_or_create_xfer(
                    src, actual_total_bytes, recv_offset
                )
                self._nixl_wrapper.transfer(xfer_handle)
                xfer_handles.append(xfer_handle)
                recv_offset += actual_total_bytes

            # Phase 3: single wait for all in-flight transfers, then unpack.
            self._wait_for_all_transfers(xfer_handles)

            with torch.cuda.stream(self._cuda_stream):
                for src, offset in recv_offsets.items():
                    byte_offset = offset
                    for dtype in self._dtypes:
                        peer_tensors = self._recv_tensors.get(
                            dtype, [[] for _ in range(self._world_size)]
                        )[src]
                        byte_offset = self._unpack_recv_buffer(
                            self._recv_buffer,
                            peer_tensors,
                            byte_offset,
                        )
        except Exception:
            self._release_all_cached_handles()
            raise
        finally:
            self._send_tensors.clear()
            self._recv_tensors.clear()