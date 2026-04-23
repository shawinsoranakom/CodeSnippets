async def forwarded_middleware(
        request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]
    ) -> StreamResponse:
        """Process forwarded data by a reverse proxy."""
        # Skip requests from Remote UI
        if remote.is_cloud_request.get():
            return await handler(request)

        # Handle X-Forwarded-For
        forwarded_for_headers: list[str] = request.headers.getall(X_FORWARDED_FOR, [])
        if not forwarded_for_headers:
            # No forwarding headers, continue as normal
            return await handler(request)

        # Get connected IP
        if (
            request.transport is None
            or request.transport.get_extra_info("peername") is None
        ):
            # Connected IP isn't retrieveable from the request transport, continue
            return await handler(request)

        connected_ip = ip_address(request.transport.get_extra_info("peername")[0])

        # We have X-Forwarded-For, but config does not agree
        if not use_x_forwarded_for:
            _LOGGER.error(
                (
                    "A request from a reverse proxy was received from %s, but your "
                    "HTTP integration is not set-up for reverse proxies"
                ),
                connected_ip,
            )
            raise HTTPBadRequest

        # Ensure the IP of the connected peer is trusted
        if not any(connected_ip in trusted_proxy for trusted_proxy in trusted_proxies):
            _LOGGER.error(
                "Received X-Forwarded-For header from an untrusted proxy %s",
                connected_ip,
            )
            raise HTTPBadRequest

        # Process multiple X-Forwarded-For from the right side (by reversing the list)
        forwarded_for_split = list(
            reversed(
                [addr for header in forwarded_for_headers for addr in header.split(",")]
            )
        )
        try:
            forwarded_for = [ip_address(addr.strip()) for addr in forwarded_for_split]
        except ValueError as err:
            _LOGGER.error(
                "Invalid IP address in X-Forwarded-For: %s", forwarded_for_headers[0]
            )
            raise HTTPBadRequest from err

        overrides: dict[str, str] = {}

        # Find the last trusted index in the X-Forwarded-For list
        forwarded_for_index = 0
        for forwarded_ip in forwarded_for:
            if any(forwarded_ip in trusted_proxy for trusted_proxy in trusted_proxies):
                forwarded_for_index += 1
                continue
            overrides["remote"] = str(forwarded_ip)
            break
        else:
            # If all the IP addresses are from trusted networks, take the left-most.
            forwarded_for_index = -1
            overrides["remote"] = str(forwarded_for[-1])

        # Handle X-Forwarded-Proto
        forwarded_proto_headers: list[str] = request.headers.getall(
            X_FORWARDED_PROTO, []
        )
        if forwarded_proto_headers:
            # Process multiple X-Forwarded-Proto from the right side (by reversing the list)
            forwarded_proto_split = list(
                reversed(
                    [
                        addr
                        for header in forwarded_proto_headers
                        for addr in header.split(",")
                    ]
                )
            )
            forwarded_proto = [proto.strip() for proto in forwarded_proto_split]

            # Catch empty values
            if "" in forwarded_proto:
                _LOGGER.error(
                    "Empty item received in X-Forward-Proto header: %s",
                    forwarded_proto_headers[0],
                )
                raise HTTPBadRequest

            # The X-Forwarded-Proto contains either one element, or the equals number
            # of elements as X-Forwarded-For
            if len(forwarded_proto) not in (1, len(forwarded_for)):
                _LOGGER.error(
                    (
                        "Incorrect number of elements in X-Forward-Proto. Expected 1 or"
                        " %d, got %d: %s"
                    ),
                    len(forwarded_for),
                    len(forwarded_proto),
                    forwarded_proto_headers[0],
                )
                raise HTTPBadRequest

            # Ideally this should take the scheme corresponding to the entry
            # in X-Forwarded-For that was chosen, but some proxies only retain
            # one element. In that case, use what we have.
            overrides["scheme"] = forwarded_proto[-1]
            if len(forwarded_proto) != 1:
                overrides["scheme"] = forwarded_proto[forwarded_for_index]

        # Handle X-Forwarded-Host
        forwarded_host_headers: list[str] = request.headers.getall(X_FORWARDED_HOST, [])
        if forwarded_host_headers:
            # Process multiple X-Forwarded-Host from the right side (by reversing the list)
            forwarded_host = list(
                reversed(
                    [
                        addr.strip()
                        for header in forwarded_host_headers
                        for addr in header.split(",")
                    ]
                )
            )[0]
            if not forwarded_host:
                _LOGGER.error("Empty value received in X-Forward-Host header")
                raise HTTPBadRequest

            overrides["host"] = forwarded_host

        # Done, create a new request based on gathered data.
        request = request.clone(**overrides)  # type: ignore[arg-type]
        return await handler(request)