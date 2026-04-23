def get_default_interfaces(self, ip_path, collected_facts=None):
        collected_facts = collected_facts or {}
        # Use the commands:
        #     ip -4 route get 8.8.8.8                     -> Google public DNS
        #     ip -6 route get 2404:6800:400a:800::1012    -> ipv6.google.com
        # to find out the default outgoing interface, address, and gateway
        command = dict(
            v4=[ip_path, '-4', 'route', 'get', '8.8.8.8'],
            v6=[ip_path, '-6', 'route', 'get', '2404:6800:400a:800::1012']
        )
        interface = dict(v4={}, v6={})

        for v in 'v4', 'v6':
            if (v == 'v6' and collected_facts.get('ansible_os_family') == 'RedHat' and
                    collected_facts.get('ansible_distribution_version', '').startswith('4.')):
                continue
            if v == 'v6' and not socket.has_ipv6:
                continue
            rc, out, err = self.module.run_command(command[v], errors='surrogate_then_replace')
            if not out:
                # v6 routing may result in
                #   RTNETLINK answers: Invalid argument
                continue
            words = out.splitlines()[0].split()
            # A valid output starts with the queried address on the first line
            if len(words) > 0 and words[0] == command[v][-1]:
                for i in range(len(words) - 1):
                    if words[i] == 'dev':
                        interface[v]['interface'] = words[i + 1]
                    elif words[i] == 'src':
                        interface[v]['address'] = words[i + 1]
                    elif words[i] == 'via' and words[i + 1] != command[v][-1]:
                        interface[v]['gateway'] = words[i + 1]
        return interface['v4'], interface['v6']