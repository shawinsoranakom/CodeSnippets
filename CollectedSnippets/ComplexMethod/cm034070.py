def get_cpu_facts(self, collected_facts=None):
        physid = 0
        sockets = {}

        cpu_facts = {}
        collected_facts = collected_facts or {}

        rc, out, err = self.module.run_command("/usr/bin/kstat cpu_info")

        cpu_facts['processor'] = []

        for line in out.splitlines():
            if len(line) < 1:
                continue

            data = line.split(None, 1)
            key = data[0].strip()

            # "brand" works on Solaris 10 & 11. "implementation" for Solaris 9.
            if key == 'module:':
                brand = ''
            elif key == 'brand':
                brand = data[1].strip()
            elif key == 'clock_MHz':
                clock_mhz = data[1].strip()
            elif key == 'implementation':
                processor = brand or data[1].strip()
                # Add clock speed to description for SPARC CPU
                # FIXME
                if collected_facts.get('ansible_machine') != 'i86pc':
                    processor += " @ " + clock_mhz + "MHz"
                if 'ansible_processor' not in collected_facts:
                    cpu_facts['processor'] = []
                cpu_facts['processor'].append(processor)
            elif key == 'chip_id':
                physid = data[1].strip()
                if physid not in sockets:
                    sockets[physid] = 1
                else:
                    sockets[physid] += 1

        # Counting cores on Solaris can be complicated.
        # https://blogs.oracle.com/mandalika/entry/solaris_show_me_the_cpu
        # Treat 'processor_count' as physical sockets and 'processor_cores' as
        # virtual CPUs visible to Solaris. Not a true count of cores for modern SPARC as
        # these processors have: sockets -> cores -> threads/virtual CPU.
        if len(sockets) > 0:
            cpu_facts['processor_count'] = len(sockets)
            cpu_facts['processor_cores'] = reduce(lambda x, y: x + y, sockets.values())
        else:
            cpu_facts['processor_cores'] = 'NA'
            cpu_facts['processor_count'] = len(cpu_facts['processor'])

        return cpu_facts