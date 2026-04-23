def get_interfaces_info(self, ifconfig_path, ifconfig_options='-a'):
        interfaces = {}
        current_if = {}
        ips = dict(
            all_ipv4_addresses=[],
            all_ipv6_addresses=[],
        )
        # FreeBSD, DragonflyBSD, NetBSD, OpenBSD and macOS all implicitly add '-a'
        # when running the command 'ifconfig'.
        # Solaris must explicitly run the command 'ifconfig -a'.
        rc, out, err = self.module.run_command([ifconfig_path, ifconfig_options])

        for line in out.splitlines():

            if line:
                words = line.split()

                if words[0] == 'pass':
                    continue
                elif re.match(r'^\S', line) and len(words) > 3:
                    current_if = self.parse_interface_line(words)
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
                elif words[0] == 'tunnel':
                    self.parse_tunnel_line(words, current_if, ips)
                else:
                    self.parse_unknown_line(words, current_if, ips)

        return interfaces, ips