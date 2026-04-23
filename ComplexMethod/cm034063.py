def get_memory_facts(self):
        memory_facts = {}

        sysctl = self.module.get_bin_path('sysctl')
        if sysctl:
            rc, out, err = self.module.run_command("%s vm.stats" % sysctl, check_rc=False)
            for line in out.splitlines():
                data = line.split()
                if 'vm.stats.vm.v_page_size' in line:
                    pagesize = int(data[1])
                if 'vm.stats.vm.v_page_count' in line:
                    pagecount = int(data[1])
                if 'vm.stats.vm.v_free_count' in line:
                    freecount = int(data[1])
            memory_facts['memtotal_mb'] = pagesize * pagecount // 1024 // 1024
            memory_facts['memfree_mb'] = pagesize * freecount // 1024 // 1024

        swapinfo = self.module.get_bin_path('swapinfo')
        if swapinfo:
            # Get swapinfo.  swapinfo output looks like:
            # Device          1M-blocks     Used    Avail Capacity
            # /dev/ada0p3        314368        0   314368     0%
            #
            rc, out, err = self.module.run_command("%s -k" % swapinfo)
            lines = out.splitlines()
            if len(lines[-1]) == 0:
                lines.pop()
            data = lines[-1].split()
            if data[0] != 'Device':
                memory_facts['swaptotal_mb'] = int(data[1]) // 1024
                memory_facts['swapfree_mb'] = int(data[3]) // 1024

        return memory_facts