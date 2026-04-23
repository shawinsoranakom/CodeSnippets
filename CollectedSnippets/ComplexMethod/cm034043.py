def assign_network_facts(self, network_facts, fsysopts_path, socket_path):
        rc, out, err = self.module.run_command([fsysopts_path, '-L', socket_path])
        # FIXME: build up a interfaces datastructure, then assign into network_facts
        network_facts['interfaces'] = []
        for i in out.split():
            if '=' in i and i.startswith('--'):
                k, v = i.split('=', 1)
                # remove '--'
                k = k[2:]
                if k == 'interface':
                    # remove /dev/ from /dev/eth0
                    v = v[5:]
                    network_facts['interfaces'].append(v)
                    network_facts[v] = {
                        'active': True,
                        'device': v,
                        'ipv4': {},
                        'ipv6': [],
                    }
                    current_if = v
                elif k == 'address':
                    network_facts[current_if]['ipv4']['address'] = v
                elif k == 'netmask':
                    network_facts[current_if]['ipv4']['netmask'] = v
                elif k == 'address6':
                    address, prefix = v.split('/')
                    network_facts[current_if]['ipv6'].append({
                        'address': address,
                        'prefix': prefix,
                    })
        return network_facts