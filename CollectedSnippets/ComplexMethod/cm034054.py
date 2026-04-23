def parse_inet_line(self, words, current_if, ips):
        # netbsd show aliases like this
        #  lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 33184
        #         inet 127.0.0.1 netmask 0xff000000
        #         inet alias 127.1.1.1 netmask 0xff000000
        if words[1] == 'alias':
            del words[1]

        address = {'address': words[1]}
        # cidr style ip address (eg, 127.0.0.1/24) in inet line
        # used in netbsd ifconfig -e output after 7.1
        if '/' in address['address']:
            ip_address, cidr_mask = address['address'].split('/')

            address['address'] = ip_address

            netmask_length = int(cidr_mask)
            netmask_bin = (1 << 32) - (1 << 32 >> int(netmask_length))
            address['netmask'] = socket.inet_ntoa(struct.pack('!L', netmask_bin))

            if len(words) > 5:
                address['broadcast'] = words[3]

        else:
            # Don't just assume columns, use "netmask" as the index for the prior column
            try:
                netmask_idx = words.index('netmask') + 1
            except ValueError:
                netmask_idx = 3

            # deal with hex netmask
            if re.match('([0-9a-f]){8}$', words[netmask_idx]):
                netmask = '0x' + words[netmask_idx]
            else:
                netmask = words[netmask_idx]

            if netmask.startswith('0x'):
                address['netmask'] = socket.inet_ntoa(struct.pack('!L', int(netmask, base=16)))
            else:
                # otherwise assume this is a dotted quad
                address['netmask'] = netmask
        # calculate the network
        address_bin = struct.unpack('!L', socket.inet_aton(address['address']))[0]
        netmask_bin = struct.unpack('!L', socket.inet_aton(address['netmask']))[0]
        address['network'] = socket.inet_ntoa(struct.pack('!L', address_bin & netmask_bin))
        if 'broadcast' not in address:
            # broadcast may be given or we need to calculate
            try:
                broadcast_idx = words.index('broadcast') + 1
            except ValueError:
                address['broadcast'] = socket.inet_ntoa(struct.pack('!L', address_bin | (~netmask_bin & 0xffffffff)))
            else:
                address['broadcast'] = words[broadcast_idx]

        # add to our list of addresses
        if not words[1].startswith('127.'):
            ips['all_ipv4_addresses'].append(address['address'])
        current_if['ipv4'].append(address)