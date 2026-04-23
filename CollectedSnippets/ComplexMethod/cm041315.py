def add(
        self,
        port: int | PortRange,
        mapped: int | PortRange = None,
        protocol: PortProtocol = "tcp",
    ):
        mapped = mapped or port
        if isinstance(port, PortRange):
            for i in range(port[1] - port[0] + 1):
                if isinstance(mapped, PortRange):
                    self.add(port[0] + i, mapped[0] + i, protocol)
                else:
                    self.add(port[0] + i, mapped, protocol)
            return
        if port is None or int(port) < 0:
            raise Exception(f"Unable to add mapping for invalid port: {port}")
        if self.contains(port, protocol):
            return
        bisected_host_port = None
        for (from_range, from_protocol), to_range in self.mappings.items():
            if not from_protocol == protocol:
                continue
            if not self.in_expanded_range(port, from_range):
                continue
            if not self.in_expanded_range(mapped, to_range):
                continue
            from_range_len = from_range[1] - from_range[0]
            to_range_len = to_range[1] - to_range[0]
            is_uniform = from_range_len == to_range_len
            if is_uniform:
                self.expand_range(port, from_range, protocol=protocol, remap=True)
                self.expand_range(mapped, to_range, protocol=protocol)
            else:
                if not self.in_range(mapped, to_range):
                    continue
                # extending a 1 to 1 mapping to be many to 1
                elif from_range_len == 1:
                    self.expand_range(port, from_range, protocol=protocol, remap=True)
                # splitting a uniform mapping
                else:
                    bisected_port_index = mapped - to_range[0]
                    bisected_host_port = from_range[0] + bisected_port_index
                    self.bisect_range(mapped, to_range, protocol=protocol)
                    self.bisect_range(bisected_host_port, from_range, protocol=protocol, remap=True)
                    break
            return
        if bisected_host_port is None:
            port_range = [port, port]
        elif bisected_host_port < port:
            port_range = [bisected_host_port, port]
        else:
            port_range = [port, bisected_host_port]
        protocol = str(protocol or "tcp").lower()
        self.mappings[(HashableList(port_range), protocol)] = [mapped, mapped]