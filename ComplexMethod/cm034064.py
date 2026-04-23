def get_memory_facts(self):
        memory_facts = {}
        if not os.access("/proc/meminfo", os.R_OK):
            return memory_facts

        memstats = {}
        for line in get_file_lines("/proc/meminfo"):
            data = line.split(":", 1)
            key = data[0]
            if key in self.ORIGINAL_MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                memory_facts["%s_mb" % key.lower()] = int(val) // 1024

            if key in self.MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                memstats[key.lower()] = int(val) // 1024

        if None not in (memstats.get('memtotal'), memstats.get('memfree')):
            memstats['real:used'] = memstats['memtotal'] - memstats['memfree']
        if None not in (memstats.get('cached'), memstats.get('memfree'), memstats.get('buffers')):
            memstats['nocache:free'] = memstats['cached'] + memstats['memfree'] + memstats['buffers']
        if None not in (memstats.get('memtotal'), memstats.get('nocache:free')):
            memstats['nocache:used'] = memstats['memtotal'] - memstats['nocache:free']
        if None not in (memstats.get('swaptotal'), memstats.get('swapfree')):
            memstats['swap:used'] = memstats['swaptotal'] - memstats['swapfree']

        memory_facts['memory_mb'] = {
            'real': {
                'total': memstats.get('memtotal'),
                'used': memstats.get('real:used'),
                'free': memstats.get('memfree'),
            },
            'nocache': {
                'free': memstats.get('nocache:free'),
                'used': memstats.get('nocache:used'),
            },
            'swap': {
                'total': memstats.get('swaptotal'),
                'free': memstats.get('swapfree'),
                'used': memstats.get('swap:used'),
                'cached': memstats.get('swapcached'),
            },
        }

        return memory_facts