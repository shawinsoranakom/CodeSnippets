def get_active_connections_count(self):
        active_connections = 0
        for p in psutil.process_iter():
            try:
                if hasattr(p, 'get_connections'):
                    connections = p.get_connections(kind='inet')
                else:
                    connections = p.connections(kind='inet')
            except psutil.Error:
                # Process is Zombie or other error state
                continue
            for conn in connections:
                if conn.status not in self.module.params['active_connection_states']:
                    continue
                if hasattr(conn, 'local_address'):
                    (local_ip, local_port) = conn.local_address
                else:
                    (local_ip, local_port) = conn.laddr
                if self.port != local_port:
                    continue
                if hasattr(conn, 'remote_address'):
                    (remote_ip, remote_port) = conn.remote_address
                else:
                    (remote_ip, remote_port) = conn.raddr
                if (conn.family, remote_ip) in self.exclude_ips:
                    continue
                if any((
                    (conn.family, local_ip) in self.ips,
                    (conn.family, self.match_all_ips[conn.family]) in self.ips,
                    local_ip.startswith(self.ipv4_mapped_ipv6_address['prefix']) and
                        (conn.family, self.ipv4_mapped_ipv6_address['match_all']) in self.ips,
                )):
                    active_connections += 1
        return active_connections