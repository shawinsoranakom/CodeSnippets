def get_active_connections_count(self):
        active_connections = 0
        for family in self.source_file.keys():
            if not os.path.isfile(self.source_file[family]):
                continue
            try:
                with open(self.source_file[family]) as f:
                    for tcp_connection in f.readlines():
                        tcp_connection = tcp_connection.strip().split()
                        if tcp_connection[self.local_address_field] == 'local_address':
                            continue
                        if (tcp_connection[self.connection_state_field] not in
                                [get_connection_state_id(_connection_state) for _connection_state in self.module.params['active_connection_states']]):
                            continue
                        (local_ip, local_port) = tcp_connection[self.local_address_field].split(':')
                        if self.port != local_port:
                            continue
                        (remote_ip, remote_port) = tcp_connection[self.remote_address_field].split(':')
                        if (family, remote_ip) in self.exclude_ips:
                            continue
                        if any((
                            (family, local_ip) in self.ips,
                            (family, self.match_all_ips[family]) in self.ips,
                            local_ip.startswith(self.ipv4_mapped_ipv6_address['prefix']) and
                                (family, self.ipv4_mapped_ipv6_address['match_all']) in self.ips,
                        )):
                            active_connections += 1
            except OSError:
                pass

        return active_connections