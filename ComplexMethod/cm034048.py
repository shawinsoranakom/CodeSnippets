def get_interfaces_info(self, ip_path, default_ipv4, default_ipv6):
        interfaces = {}
        ips = dict(
            all_ipv4_addresses=[],
            all_ipv6_addresses=[],
        )

        # FIXME: maybe split into smaller methods?
        # FIXME: this is pretty much a constructor

        for path in glob.glob('/sys/class/net/*'):
            if not os.path.isdir(path):
                continue
            device = os.path.basename(path)
            interfaces[device] = {'device': device}
            if os.path.exists(os.path.join(path, 'address')):
                macaddress = get_file_content(os.path.join(path, 'address'), default='')
                if macaddress and macaddress != '00:00:00:00:00:00':
                    interfaces[device]['macaddress'] = macaddress
            if os.path.exists(os.path.join(path, 'mtu')):
                interfaces[device]['mtu'] = int(get_file_content(os.path.join(path, 'mtu')))
            if os.path.exists(os.path.join(path, 'operstate')):
                interfaces[device]['active'] = get_file_content(os.path.join(path, 'operstate')) != 'down'
            if os.path.exists(os.path.join(path, 'device', 'driver', 'module')):
                interfaces[device]['module'] = os.path.basename(os.path.realpath(os.path.join(path, 'device', 'driver', 'module')))
            if os.path.exists(os.path.join(path, 'type')):
                _type = get_file_content(os.path.join(path, 'type'))
                interfaces[device]['type'] = self.INTERFACE_TYPE.get(_type, 'unknown')
            if os.path.exists(os.path.join(path, 'bridge')):
                interfaces[device]['type'] = 'bridge'
                interfaces[device]['interfaces'] = [os.path.basename(b) for b in glob.glob(os.path.join(path, 'brif', '*'))]
                if os.path.exists(os.path.join(path, 'bridge', 'bridge_id')):
                    interfaces[device]['id'] = get_file_content(os.path.join(path, 'bridge', 'bridge_id'), default='')
                if os.path.exists(os.path.join(path, 'bridge', 'stp_state')):
                    interfaces[device]['stp'] = get_file_content(os.path.join(path, 'bridge', 'stp_state')) == '1'
            if os.path.exists(os.path.join(path, 'bonding')):
                interfaces[device]['type'] = 'bonding'
                interfaces[device]['slaves'] = get_file_content(os.path.join(path, 'bonding', 'slaves'), default='').split()
                interfaces[device]['mode'] = get_file_content(os.path.join(path, 'bonding', 'mode'), default='').split()[0]
                interfaces[device]['miimon'] = get_file_content(os.path.join(path, 'bonding', 'miimon'), default='').split()[0]
                interfaces[device]['lacp_rate'] = get_file_content(os.path.join(path, 'bonding', 'lacp_rate'), default='').split()[0]
                primary = get_file_content(os.path.join(path, 'bonding', 'primary'))
                if primary:
                    interfaces[device]['primary'] = primary
                    path = os.path.join(path, 'bonding', 'all_slaves_active')
                    if os.path.exists(path):
                        interfaces[device]['all_slaves_active'] = get_file_content(path) == '1'
            if os.path.exists(os.path.join(path, 'bonding_slave')):
                interfaces[device]['perm_macaddress'] = get_file_content(os.path.join(path, 'bonding_slave', 'perm_hwaddr'), default='')
            if os.path.exists(os.path.join(path, 'device')):
                interfaces[device]['pciid'] = os.path.basename(os.readlink(os.path.join(path, 'device')))
            if os.path.exists(os.path.join(path, 'speed')):
                speed = get_file_content(os.path.join(path, 'speed'))
                if speed is not None:
                    interfaces[device]['speed'] = int(speed)

            # Check whether an interface is in promiscuous mode
            if os.path.exists(os.path.join(path, 'flags')):
                promisc_mode = False
                # The second byte indicates whether the interface is in promiscuous mode.
                # 1 = promisc
                # 0 = no promisc
                data = int(get_file_content(os.path.join(path, 'flags')), 16)
                promisc_mode = (data & 0x0100 > 0)
                interfaces[device]['promisc'] = promisc_mode

            # TODO: determine if this needs to be in a nested scope/closure
            def parse_ip_output(output, secondary=False):
                for line in output.splitlines():
                    if not line:
                        continue
                    words = line.split()
                    broadcast = ''
                    if words[0] == 'inet':
                        if '/' in words[1]:
                            address, netmask_length = words[1].split('/')
                            if len(words) > 3:
                                if words[2] == 'brd':
                                    broadcast = words[3]
                        else:
                            # pointopoint interfaces do not have a prefix
                            address = words[1]
                            netmask_length = "32"
                        address_bin = struct.unpack('!L', socket.inet_aton(address))[0]
                        netmask_bin = (1 << 32) - (1 << 32 >> int(netmask_length))
                        netmask = socket.inet_ntoa(struct.pack('!L', netmask_bin))
                        network = socket.inet_ntoa(struct.pack('!L', address_bin & netmask_bin))
                        iface = words[-1]
                        # NOTE: device is ref to outside scope
                        # NOTE: interfaces is also ref to outside scope
                        if iface != device:
                            interfaces[iface] = {}
                        if not secondary and "ipv4" not in interfaces[iface]:
                            interfaces[iface]['ipv4'] = {'address': address,
                                                         'broadcast': broadcast,
                                                         'netmask': netmask,
                                                         'network': network,
                                                         'prefix': netmask_length,
                                                         }
                        else:
                            if "ipv4_secondaries" not in interfaces[iface]:
                                interfaces[iface]["ipv4_secondaries"] = []
                            interfaces[iface]["ipv4_secondaries"].append({
                                'address': address,
                                'broadcast': broadcast,
                                'netmask': netmask,
                                'network': network,
                                'prefix': netmask_length,
                            })

                        # add this secondary IP to the main device
                        if secondary:
                            if "ipv4_secondaries" not in interfaces[device]:
                                interfaces[device]["ipv4_secondaries"] = []
                            if device != iface:
                                interfaces[device]["ipv4_secondaries"].append({
                                    'address': address,
                                    'broadcast': broadcast,
                                    'netmask': netmask,
                                    'network': network,
                                    'prefix': netmask_length,
                                })

                        # NOTE: default_ipv4 is ref to outside scope
                        # If this is the default address, update default_ipv4
                        if 'address' in default_ipv4 and default_ipv4['address'] == address:
                            default_ipv4['broadcast'] = broadcast
                            default_ipv4['netmask'] = netmask
                            default_ipv4['network'] = network
                            default_ipv4['prefix'] = netmask_length
                            # NOTE: macaddress is ref from outside scope
                            default_ipv4['macaddress'] = macaddress
                            default_ipv4['mtu'] = interfaces[device]['mtu']
                            default_ipv4['type'] = interfaces[device].get("type", "unknown")
                            default_ipv4['alias'] = words[-1]
                        if not address.startswith('127.'):
                            ips['all_ipv4_addresses'].append(address)
                    elif words[0] == 'inet6':
                        if 'peer' == words[2]:
                            address = words[1]
                            dummy, prefix = words[3].split('/')
                            scope = words[5]
                        else:
                            address, prefix = words[1].split('/')
                            scope = words[3]
                        if 'ipv6' not in interfaces[device]:
                            interfaces[device]['ipv6'] = []
                        interfaces[device]['ipv6'].append({
                            'address': address,
                            'prefix': prefix,
                            'scope': scope
                        })
                        # If this is the default address, update default_ipv6
                        if 'address' in default_ipv6 and default_ipv6['address'] == address:
                            default_ipv6['prefix'] = prefix
                            default_ipv6['scope'] = scope
                            default_ipv6['macaddress'] = macaddress
                            default_ipv6['mtu'] = interfaces[device]['mtu']
                            default_ipv6['type'] = interfaces[device].get("type", "unknown")
                        if not address == '::1':
                            ips['all_ipv6_addresses'].append(address)

            args = [ip_path, 'addr', 'show', 'primary', 'dev', device]
            rc, primary_data, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                parse_ip_output(primary_data)
            else:
                # possibly busybox, fallback to running without the "primary" arg
                # https://github.com/ansible/ansible/issues/50871
                args = [ip_path, 'addr', 'show', 'dev', device]
                rc, data, stderr = self.module.run_command(args, errors='surrogate_then_replace')
                if rc == 0:
                    parse_ip_output(data)

            args = [ip_path, 'addr', 'show', 'secondary', 'dev', device]
            rc, secondary_data, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                parse_ip_output(secondary_data, secondary=True)

            interfaces[device].update(self.get_ethtool_data(device))

        # replace : by _ in interface name since they are hard to use in template
        new_interfaces = {}
        # i is a dict key (string) not an index int
        for i in interfaces:
            if ':' in i:
                new_interfaces[i.replace(':', '_')] = interfaces[i]
            else:
                new_interfaces[i] = interfaces[i]
        return new_interfaces, ips