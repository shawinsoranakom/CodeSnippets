def recv_tensor(
        self,
        tensor_id: str,
        remote_address: str | None = None,
    ) -> torch.Tensor:
        if self.send_type == "PUT" or self.send_type == "PUT_ASYNC":
            start_time = time.time()
            with self.recv_store_cv:
                while tensor_id not in self.recv_store:
                    self.recv_store_cv.wait()
                tensor = self.recv_store[tensor_id]

            if tensor is not None:
                if isinstance(tensor, tuple):
                    addr, dtype, shape = tensor
                    tensor = self.pool.load_tensor(addr, dtype, shape, self.device)
                else:
                    self.buffer_size -= tensor.element_size() * tensor.numel()
            else:
                duration = time.time() - start_time
                logger.warning(
                    "🔴[PUT]Recv From %s, tensor_id:%s, duration:%.3fms, rank:%d",
                    remote_address,
                    tensor_id,
                    duration * 1000,
                    self.rank,
                )
            return tensor

        # GET
        if remote_address is None:
            return None

        if remote_address not in self.socks:
            self.create_connect(remote_address)

        sock = self.socks[remote_address]
        comm, rank = self.comms[remote_address]

        data = {"cmd": "GET", "tensor_id": tensor_id}
        sock.send(msgpack.dumps(data))

        message = sock.recv()
        data = msgpack.loads(message)
        if data["ret"] != 0:
            logger.warning(
                "🔴[GET]Recv From %s, tensor_id: %s, ret: %d",
                remote_address,
                tensor_id,
                data["ret"],
            )
            return None

        with torch.cuda.stream(self.recv_stream):
            tensor = torch.empty(
                data["shape"], dtype=getattr(torch, data["dtype"]), device=self.device
            )

        self.recv(comm, tensor, rank ^ 1, self.recv_stream)

        return tensor