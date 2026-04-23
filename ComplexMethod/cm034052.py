def get_default_interfaces(self, route_path):

        # Use the commands:
        #     route -n get default
        #     route -n get -inet6 default
        # to find out the default outgoing interface, address, and gateway

        command = dict(v4=[route_path, '-n', 'get', 'default'],
                       v6=[route_path, '-n', 'get', '-inet6', 'default'])

        interface = dict(v4={}, v6={})

        for v in 'v4', 'v6':

            if v == 'v6' and not socket.has_ipv6:
                continue
            rc, out, err = self.module.run_command(command[v])
            if not out:
                # v6 routing may result in
                #   RTNETLINK answers: Invalid argument
                continue
            for line in out.splitlines():
                words = line.strip().split(': ')
                # Collect output from route command
                if len(words) > 1:
                    if words[0] == 'interface':
                        interface[v]['interface'] = words[1]
                    if words[0] == 'gateway':
                        interface[v]['gateway'] = words[1]
                    # help pick the right interface address on OpenBSD
                    if words[0] == 'if address':
                        interface[v]['address'] = words[1]
                    # help pick the right interface address on NetBSD
                    if words[0] == 'local addr':
                        interface[v]['address'] = words[1]

        return interface['v4'], interface['v6']