def send_notify(self, req_ids, remote_ip, remote_port):
        if not remote_ip or not remote_port:
            logger.warning("Missing remote_ip or remote_port for notification")
            return

        path = make_zmq_path("tcp", remote_ip, remote_port)

        if path not in self.paths:
            ctx = zmq.Context.instance()
            sock = make_zmq_socket(
                ctx=ctx, path=path, socket_type=zmq.DEALER, bind=False
            )
            self.paths[path] = sock

        req_list = req_ids if isinstance(req_ids, list) else [req_ids]

        sock = self.paths[path]
        try:
            for req_id in req_list:
                if not isinstance(req_id, str):
                    logger.warning(
                        "Invalid req_id type: %s, expected str", type(req_id)
                    )
                    continue
                sock.send(req_id.encode("utf-8"))
        except Exception as e:
            logger.error("Failed to send notification to %s: %s", path, e)
            self.paths.pop(path, None)
            raise