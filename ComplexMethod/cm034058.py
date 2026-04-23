def get_dmi_facts(self):
        dmi_facts = {}

        rc, out, err = self.module.run_command("/usr/sbin/lsattr -El sys0 -a fwversion")
        data = out.split()
        dmi_facts['firmware_version'] = data[1].strip('IBM,')
        lsconf_path = self.module.get_bin_path("lsconf")
        if lsconf_path:
            rc, out, err = self.module.run_command(lsconf_path)
            if rc == 0 and out:
                for line in out.splitlines():
                    data = line.split(':')
                    if 'Machine Serial Number' in line:
                        dmi_facts['product_serial'] = data[1].strip()
                    if 'LPAR Info' in line:
                        dmi_facts['lpar_info'] = data[1].strip()
                    if 'System Model' in line:
                        dmi_facts['product_name'] = data[1].strip()
        return dmi_facts