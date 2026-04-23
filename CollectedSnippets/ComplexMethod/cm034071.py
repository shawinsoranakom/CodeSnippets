def get_device_facts(self):
        # Device facts are derived for sdderr kstats. This code does not use the
        # full output, but rather queries for specific stats.
        # Example output:
        # sderr:0:sd0,err:Hard Errors     0
        # sderr:0:sd0,err:Illegal Request 6
        # sderr:0:sd0,err:Media Error     0
        # sderr:0:sd0,err:Predictive Failure Analysis     0
        # sderr:0:sd0,err:Product VBOX HARDDISK   9
        # sderr:0:sd0,err:Revision        1.0
        # sderr:0:sd0,err:Serial No       VB0ad2ec4d-074a
        # sderr:0:sd0,err:Size    53687091200
        # sderr:0:sd0,err:Soft Errors     0
        # sderr:0:sd0,err:Transport Errors        0
        # sderr:0:sd0,err:Vendor  ATA

        device_facts = {}
        device_facts['devices'] = {}

        disk_stats = {
            'Product': 'product',
            'Revision': 'revision',
            'Serial No': 'serial',
            'Size': 'size',
            'Vendor': 'vendor',
            'Hard Errors': 'hard_errors',
            'Soft Errors': 'soft_errors',
            'Transport Errors': 'transport_errors',
            'Media Error': 'media_errors',
            'Predictive Failure Analysis': 'predictive_failure_analysis',
            'Illegal Request': 'illegal_request',
        }

        cmd = ['/usr/bin/kstat', '-p']

        for ds in disk_stats:
            cmd.append('sderr:::%s' % ds)

        d = {}
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            return device_facts

        sd_instances = frozenset(line.split(':')[1] for line in out.split('\n') if line.startswith('sderr'))
        for instance in sd_instances:
            lines = (line for line in out.split('\n') if ':' in line and line.split(':')[1] == instance)
            for line in lines:
                text, value = line.split('\t')
                stat = text.split(':')[3]

                if stat == 'Size':
                    d[disk_stats.get(stat)] = bytes_to_human(float(value))
                else:
                    d[disk_stats.get(stat)] = value.rstrip()

            diskname = 'sd' + instance
            device_facts['devices'][diskname] = d
            d = {}

        return device_facts