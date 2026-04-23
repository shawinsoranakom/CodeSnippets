def _cfg(cfg: ContainerConfiguration):
            if not params:
                return

            for port_mapping in params:
                port_split = port_mapping.split(":")
                protocol = "tcp"
                if len(port_split) == 1:
                    host_port = container_port = port_split[0]
                elif len(port_split) == 2:
                    host_port, container_port = port_split
                elif len(port_split) == 3:
                    _, host_port, container_port = port_split
                else:
                    raise ValueError(f"Invalid port string provided: {port_mapping}")

                host_port_split = host_port.split("-")
                if len(host_port_split) == 2:
                    host_port = [int(host_port_split[0]), int(host_port_split[1])]
                elif len(host_port_split) == 1:
                    host_port = int(host_port)
                else:
                    raise ValueError(f"Invalid port string provided: {port_mapping}")

                if "/" in container_port:
                    container_port, protocol = container_port.split("/")

                container_port_split = container_port.split("-")
                if len(container_port_split) == 2:
                    container_port = [int(container_port_split[0]), int(container_port_split[1])]
                elif len(container_port_split) == 1:
                    container_port = int(container_port)
                else:
                    raise ValueError(f"Invalid port string provided: {port_mapping}")

                cfg.ports.add(host_port, container_port, protocol)