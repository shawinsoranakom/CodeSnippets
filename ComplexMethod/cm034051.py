def get_interfaces_info(self, ifconfig_path):
        interfaces = {}
        current_if = {}
        ips = dict(
            all_ipv4_addresses=[],
            all_ipv6_addresses=[],
        )
        rc, out, err = self.module.run_command([ifconfig_path, '-a'])

        for line in out.splitlines():

            if line:
                words = line.split()

                if re.match(r'^\S', line) and len(words) > 3:
                    current_if = self.parse_interface_line(words, current_if, interfaces)
                    interfaces[current_if['device']] = current_if
                elif words[0].startswith('options='):
                    self.parse_options_line(words, current_if, ips)
                elif words[0] == 'nd6':
                    self.parse_nd6_line(words, current_if, ips)
                elif words[0] == 'ether':
                    self.parse_ether_line(words, current_if, ips)
                elif words[0] == 'media:':
                    self.parse_media_line(words, current_if, ips)
                elif words[0] == 'status:':
                    self.parse_status_line(words, current_if, ips)
                elif words[0] == 'lladdr':
                    self.parse_lladdr_line(words, current_if, ips)
                elif words[0] == 'inet':
                    self.parse_inet_line(words, current_if, ips)
                elif words[0] == 'inet6':
                    self.parse_inet6_line(words, current_if, ips)
                else:
                    self.parse_unknown_line(words, current_if, ips)

        # 'parse_interface_line' and 'parse_inet*_line' leave two dicts in the
        # ipv4/ipv6 lists which is ugly and hard to read.
        # This quick hack merges the dictionaries. Purely cosmetic.
        for iface in interfaces:
            for v in 'ipv4', 'ipv6':
                combined_facts = {}
                for facts in interfaces[iface][v]:
                    combined_facts.update(facts)
                if len(combined_facts.keys()) > 0:
                    interfaces[iface][v] = [combined_facts]

        return interfaces, ips