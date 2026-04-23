def listen_for_requests(self):
        while True:
            socks = dict(self.poller.poll())
            if self.router_socket not in socks:
                continue

            remote_address, message = self.router_socket.recv_multipart()
            data = msgpack.loads(message)
            if data["cmd"] == "NEW":
                unique_id = self.nccl.unique_id_from_bytes(bytes(data["unique_id"]))
                with torch.accelerator.device_index(self.device.index):
                    rank = 1
                    with set_p2p_nccl_context(self.nccl_num_channels):
                        comm: ncclComm_t = self.nccl.ncclCommInitRank(
                            2, unique_id, rank
                        )
                    self.comms[remote_address.decode()] = (comm, rank)
                    logger.info(
                        "🤝ncclCommInitRank Success, %s👈%s, MyRank:%s",
                        self.zmq_address,
                        remote_address.decode(),
                        rank,
                    )
            elif data["cmd"] == "PUT":
                tensor_id = data["tensor_id"]
                try:
                    with torch.cuda.stream(self.recv_stream):
                        tensor = torch.empty(
                            data["shape"],
                            dtype=getattr(torch, data["dtype"]),
                            device=self.device,
                        )
                    self.router_socket.send_multipart([remote_address, b"0"])
                    comm, rank = self.comms[remote_address.decode()]
                    self.recv(comm, tensor, rank ^ 1, self.recv_stream)
                    tensor_size = tensor.element_size() * tensor.numel()
                    if self.buffer_size + tensor_size > self.buffer_size_threshold:
                        # Store Tensor in memory pool
                        addr = self.pool.store_tensor(tensor)
                        tensor = (addr, tensor.dtype, tensor.shape)
                        logger.warning(
                            "🔴[PUT]Recv Tensor, Out Of Threshold, "
                            "%s👈%s, data:%s, addr:%d",
                            self.zmq_address,
                            remote_address.decode(),
                            data,
                            addr,
                        )
                    else:
                        self.buffer_size += tensor_size

                except torch.cuda.OutOfMemoryError:
                    self.router_socket.send_multipart([remote_address, b"1"])
                    tensor = None
                    logger.warning(
                        "🔴[PUT]Recv Tensor, Out Of Memory, %s👈%s, data:%s",
                        self.zmq_address,
                        remote_address.decode(),
                        data,
                    )

                with self.recv_store_cv:
                    self.recv_store[tensor_id] = tensor
                    self.have_received_tensor_id(tensor_id)
                    self.recv_store_cv.notify()

            elif data["cmd"] == "GET":
                tensor_id = data["tensor_id"]
                with self.send_store_cv:
                    tensor = self.send_store.pop(tensor_id, None)
                    if tensor is not None:
                        data = {
                            "ret": 0,
                            "shape": tensor.shape,
                            "dtype": str(tensor.dtype).replace("torch.", ""),
                        }
                        # LRU
                        self.send_store[tensor_id] = tensor
                        self.have_sent_tensor_id(tensor_id)
                    else:
                        data = {"ret": 1}

                self.router_socket.send_multipart([remote_address, msgpack.dumps(data)])

                if data["ret"] == 0:
                    comm, rank = self.comms[remote_address.decode()]
                    self.send(comm, tensor.to(self.device), rank ^ 1, self.send_stream)
            else:
                logger.warning(
                    "🚧Unexpected, Received message from %s, data:%s",
                    remote_address,
                    data,
                )