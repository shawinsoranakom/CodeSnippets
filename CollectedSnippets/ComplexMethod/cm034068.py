def get_device_facts(self):
        device_facts = {}

        device_facts['devices'] = {}
        lspci = self.module.get_bin_path('lspci')
        if lspci:
            rc, pcidata, err = self.module.run_command([lspci, '-D'], errors='surrogate_then_replace')
        else:
            pcidata = None

        try:
            block_devs = os.listdir("/sys/block")
        except OSError:
            return device_facts

        devs_wwn = {}
        try:
            devs_by_id = os.listdir("/dev/disk/by-id")
        except OSError:
            pass
        else:
            for link_name in devs_by_id:
                if link_name.startswith("wwn-"):
                    try:
                        wwn_link = os.readlink(os.path.join("/dev/disk/by-id", link_name))
                    except OSError:
                        continue
                    devs_wwn[os.path.basename(wwn_link)] = link_name[4:]

        links = self.get_all_device_links()
        device_facts['device_links'] = links

        for block in block_devs:
            virtual = 1
            sysfs_no_links = 0
            try:
                path = os.readlink(os.path.join("/sys/block/", block))
            except OSError:
                e = sys.exc_info()[1]
                if e.errno == errno.EINVAL:
                    path = block
                    sysfs_no_links = 1
                else:
                    continue
            sysdir = os.path.join("/sys/block", path)
            if sysfs_no_links == 1:
                for folder in os.listdir(sysdir):
                    if "device" in folder:
                        virtual = 0
                        break
            d = {}
            d['virtual'] = virtual
            d['links'] = {}
            for (link_type, link_values) in links.items():
                d['links'][link_type] = link_values.get(block, [])
            diskname = os.path.basename(sysdir)
            for key in ['vendor', 'model', 'sas_address', 'sas_device_handle']:
                d[key] = get_file_content(sysdir + "/device/" + key)

            sg_inq = self.module.get_bin_path('sg_inq')

            # we can get NVMe device's serial number from /sys/block/<name>/device/serial
            serial_path = "/sys/block/%s/device/serial" % (block)

            if sg_inq:
                serial = self._get_sg_inq_serial(sg_inq, block)
                if serial:
                    d['serial'] = serial
            else:
                serial = get_file_content(serial_path)
                if serial:
                    d['serial'] = serial

            d['removable'] = get_file_content(sysdir + '/removable')

            # Historically, `support_discard` simply returned the value of
            # `/sys/block/{device}/queue/discard_granularity`. When its value
            # is `0`, then the block device doesn't support discards;
            # _however_, it being greater than zero doesn't necessarily mean
            # that the block device _does_ support discards.
            #
            # Another indication that a block device doesn't support discards
            # is `/sys/block/{device}/queue/discard_max_hw_bytes` being equal
            # to `0` (with the same caveat as above). So if either of those are
            # `0`, set `support_discard` to zero, otherwise set it to the value
            # of `discard_granularity` for backwards compatibility.
            d['support_discard'] = (
                '0'
                if get_file_content(sysdir + '/queue/discard_max_hw_bytes') == '0'
                else get_file_content(sysdir + '/queue/discard_granularity')
            )

            if diskname in devs_wwn:
                d['wwn'] = devs_wwn[diskname]

            d['partitions'] = {}
            for folder in os.listdir(sysdir):
                m = re.search("(" + diskname + r"[p]?\d+)", folder)
                if m:
                    part = {}
                    partname = m.group(1)
                    part_sysdir = sysdir + "/" + partname

                    part['links'] = {}
                    for (link_type, link_values) in links.items():
                        part['links'][link_type] = link_values.get(partname, [])

                    part['start'] = get_file_content(part_sysdir + "/start", 0)
                    part['sectorsize'] = get_file_content(part_sysdir + "/queue/logical_block_size")
                    if not part['sectorsize']:
                        part['sectorsize'] = get_file_content(part_sysdir + "/queue/hw_sector_size", 512)
                    # sysfs sectorcount assumes 512 blocksize. Convert using the correct sectorsize
                    part['sectors'] = int(get_file_content(part_sysdir + "/size", 0)) * 512 // int(part['sectorsize'])
                    part['size'] = bytes_to_human(float(part['sectors']) * float(part['sectorsize']))
                    part['uuid'] = get_partition_uuid(partname)
                    self.get_holders(part, part_sysdir)

                    d['partitions'][partname] = part

            d['rotational'] = get_file_content(sysdir + "/queue/rotational")
            d['scheduler_mode'] = ""
            scheduler = get_file_content(sysdir + "/queue/scheduler")
            if scheduler is not None:
                m = re.match(r".*?(\[(.*)\])", scheduler)
                if m:
                    d['scheduler_mode'] = m.group(2)

            d['sectorsize'] = get_file_content(sysdir + "/queue/logical_block_size")
            if not d['sectorsize']:
                d['sectorsize'] = get_file_content(sysdir + "/queue/hw_sector_size", 512)
            # sysfs sectorcount assumes 512 blocksize. Convert using the correct sectorsize
            d['sectors'] = int(get_file_content(sysdir + "/size")) * 512 // int(d['sectorsize'])
            if not d['sectors']:
                d['sectors'] = 0
            d['size'] = bytes_to_human(float(d['sectors']) * float(d['sectorsize']))

            d['host'] = ""

            # domains are numbered (0 to ffff), bus (0 to ff), slot (0 to 1f), and function (0 to 7).
            m = re.match(r".+/([a-f0-9]{4}:[a-f0-9]{2}:[0|1][a-f0-9]\.[0-7])/", sysdir)
            if m and pcidata:
                pciid = m.group(1)
                did = re.escape(pciid)
                m = re.search("^" + did + r"\s(.*)$", pcidata, re.MULTILINE)
                if m:
                    d['host'] = m.group(1)

            self.get_holders(d, sysdir)

            device_facts['devices'][diskname] = d

        return device_facts