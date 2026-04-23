def get_dmi_facts(self):
        """ learn dmi facts from system

        Try /sys first for dmi related facts.
        If that is not available, fall back to dmidecode executable """

        dmi_facts = {}

        if os.path.exists('/sys/devices/virtual/dmi/id/product_name'):
            # Use kernel DMI info, if available

            # DMI SPEC -- https://www.dmtf.org/sites/default/files/standards/documents/DSP0134_3.2.0.pdf
            FORM_FACTOR = ["Unknown", "Other", "Unknown", "Desktop",
                           "Low Profile Desktop", "Pizza Box", "Mini Tower", "Tower",
                           "Portable", "Laptop", "Notebook", "Hand Held", "Docking Station",
                           "All In One", "Sub Notebook", "Space-saving", "Lunch Box",
                           "Main Server Chassis", "Expansion Chassis", "Sub Chassis",
                           "Bus Expansion Chassis", "Peripheral Chassis", "RAID Chassis",
                           "Rack Mount Chassis", "Sealed-case PC", "Multi-system",
                           "CompactPCI", "AdvancedTCA", "Blade", "Blade Enclosure",
                           "Tablet", "Convertible", "Detachable", "IoT Gateway",
                           "Embedded PC", "Mini PC", "Stick PC"]

            DMI_DICT = {
                'bios_date': '/sys/devices/virtual/dmi/id/bios_date',
                'bios_vendor': '/sys/devices/virtual/dmi/id/bios_vendor',
                'bios_version': '/sys/devices/virtual/dmi/id/bios_version',
                'board_asset_tag': '/sys/devices/virtual/dmi/id/board_asset_tag',
                'board_name': '/sys/devices/virtual/dmi/id/board_name',
                'board_serial': '/sys/devices/virtual/dmi/id/board_serial',
                'board_vendor': '/sys/devices/virtual/dmi/id/board_vendor',
                'board_version': '/sys/devices/virtual/dmi/id/board_version',
                'chassis_asset_tag': '/sys/devices/virtual/dmi/id/chassis_asset_tag',
                'chassis_serial': '/sys/devices/virtual/dmi/id/chassis_serial',
                'chassis_vendor': '/sys/devices/virtual/dmi/id/chassis_vendor',
                'chassis_version': '/sys/devices/virtual/dmi/id/chassis_version',
                'form_factor': '/sys/devices/virtual/dmi/id/chassis_type',
                'product_name': '/sys/devices/virtual/dmi/id/product_name',
                'product_serial': '/sys/devices/virtual/dmi/id/product_serial',
                'product_uuid': '/sys/devices/virtual/dmi/id/product_uuid',
                'product_version': '/sys/devices/virtual/dmi/id/product_version',
                'system_vendor': '/sys/devices/virtual/dmi/id/sys_vendor',
            }

            for (key, path) in DMI_DICT.items():
                data = get_file_content(path)
                if data is not None:
                    if key == 'form_factor':
                        try:
                            dmi_facts['form_factor'] = FORM_FACTOR[int(data)]
                        except IndexError:
                            dmi_facts['form_factor'] = 'unknown (%s)' % data
                    else:
                        dmi_facts[key] = data
                else:
                    dmi_facts[key] = 'NA'

        else:
            # Fall back to using dmidecode, if available
            DMI_DICT = {
                'bios_date': 'bios-release-date',
                'bios_vendor': 'bios-vendor',
                'bios_version': 'bios-version',
                'board_asset_tag': 'baseboard-asset-tag',
                'board_name': 'baseboard-product-name',
                'board_serial': 'baseboard-serial-number',
                'board_vendor': 'baseboard-manufacturer',
                'board_version': 'baseboard-version',
                'chassis_asset_tag': 'chassis-asset-tag',
                'chassis_serial': 'chassis-serial-number',
                'chassis_vendor': 'chassis-manufacturer',
                'chassis_version': 'chassis-version',
                'form_factor': 'chassis-type',
                'product_name': 'system-product-name',
                'product_serial': 'system-serial-number',
                'product_uuid': 'system-uuid',
                'product_version': 'system-version',
                'system_vendor': 'system-manufacturer',
            }
            dmi_bin = self.module.get_bin_path('dmidecode')
            if dmi_bin is None:
                dmi_facts = dict.fromkeys(
                    DMI_DICT.keys(),
                    'NA'
                )
                return dmi_facts

            for (k, v) in DMI_DICT.items():
                (rc, out, err) = self.module.run_command('%s -s %s' % (dmi_bin, v))
                if rc == 0:
                    # Strip out commented lines (specific dmidecode output)
                    thisvalue = ''.join([line for line in out.splitlines() if not line.startswith('#')])
                    try:
                        json.dumps(thisvalue)
                    except UnicodeDecodeError:
                        thisvalue = "NA"

                    dmi_facts[k] = thisvalue
                else:
                    dmi_facts[k] = 'NA'

        return dmi_facts