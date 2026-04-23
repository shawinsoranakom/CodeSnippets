def _listen_for_register(hostname, port):
    context = zmq.Context()
    router_socket = context.socket(zmq.ROUTER)
    router_socket.bind(f"tcp://{hostname}:{port}")
    poller = zmq.Poller()
    poller.register(router_socket, zmq.POLLIN)
    global prefill_instances
    global decode_instances

    while True:
        socks = dict(poller.poll())
        if router_socket in socks:
            remote_addr, msg = router_socket.recv_multipart()
            data = msgpack.loads(msg)
            if data.get("type") == "HELLO":
                pass
            elif data.get("type") in ("P", "D"):
                role = data["type"]
                required_keys = {
                    "http_address",
                    "zmq_address",
                    "dp_size",
                    "tp_size",
                    "transfer_mode",
                }
                missing = required_keys - data.keys()
                if missing:
                    logger.error(
                        "Registration message missing required keys %s; skipping",
                        missing,
                    )
                    continue
                # Derive request_address from http_address
                # api path suffix is appended at request time
                instance = {
                    "role": role,
                    "request_address": f"http://{data['http_address']}/v1",
                    "http_address": data["http_address"],
                    "zmq_address": data["zmq_address"],
                    "dp_size": data["dp_size"],
                    "tp_size": data["tp_size"],
                    "transfer_mode": data["transfer_mode"],
                }
                # zmq_address format: "host:IP,handshake:PORT,notify:PORT"
                # Stored verbatim; embedded into the request_id by handle_request.

                global TRANSFER_TYPE
                transfer_mode = instance["transfer_mode"]
                target_list = prefill_instances if role == "P" else decode_instances
                with _list_lock:
                    if TRANSFER_TYPE is None:
                        TRANSFER_TYPE = transfer_mode
                        logger.info("SET TRANSFER TYPE TO %s", TRANSFER_TYPE)
                    elif transfer_mode != TRANSFER_TYPE:
                        logger.error(
                            "Mismatched transfer mode: expected %s, got %s;"
                            " skipping registration of %s",
                            TRANSFER_TYPE,
                            transfer_mode,
                            data["http_address"],
                        )
                        continue
                    existing_idx = next(
                        (
                            idx
                            for idx, i in enumerate(target_list)
                            if i.get("http_address") == data["http_address"]
                        ),
                        None,
                    )
                    if existing_idx is not None:
                        target_list[existing_idx] = instance
                        logger.info(
                            "Updated existing %s instance: %s",
                            "Prefill" if role == "P" else "Decode",
                            instance,
                        )
                    else:
                        target_list.append(instance)
                        logger.info(
                            "Registered %s instance: %s",
                            "Prefill" if role == "P" else "Decode",
                            instance,
                        )
            else:
                logger.warning(
                    "Received message with unrecognized type %r; ignoring",
                    data.get("type"),
                )