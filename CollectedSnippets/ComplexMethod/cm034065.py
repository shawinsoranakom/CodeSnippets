def get_cpu_facts(self, collected_facts=None):
        cpu_facts = {}
        collected_facts = collected_facts or {}

        i = 0
        vendor_id_occurrence = 0
        model_name_occurrence = 0
        processor_occurrence = 0
        physid = 0
        coreid = 0
        sockets = {}
        cores = {}
        zp = 0
        zmt = 0

        xen = False
        xen_paravirt = False
        try:
            if os.path.exists('/proc/xen'):
                xen = True
            else:
                for line in get_file_lines('/sys/hypervisor/type'):
                    if line.strip() == 'xen':
                        xen = True
                    # Only interested in the first line
                    break
        except OSError:
            pass

        if not os.access("/proc/cpuinfo", os.R_OK):
            return cpu_facts

        cpu_facts['processor'] = []
        for line in get_file_lines('/proc/cpuinfo'):
            data = line.split(":", 1)
            key = data[0].strip()

            try:
                val = data[1].strip()
            except IndexError:
                val = ""

            if xen:
                if key == 'flags':
                    # Check for vme cpu flag, Xen paravirt does not expose this.
                    #   Need to detect Xen paravirt because it exposes cpuinfo
                    #   differently than Xen HVM or KVM and causes reporting of
                    #   only a single cpu core.
                    if 'vme' not in val:
                        xen_paravirt = True

            if key == "flags":
                cpu_facts['flags'] = val.split()

            # model name is for Intel arch, Processor (mind the uppercase P)
            # works for some ARM devices, like the Sheevaplug.
            if key in ['model name', 'Processor', 'vendor_id', 'cpu', 'Vendor', 'processor']:
                if 'processor' not in cpu_facts:
                    cpu_facts['processor'] = []
                cpu_facts['processor'].append(val)
                if key == 'vendor_id':
                    vendor_id_occurrence += 1
                if key == 'model name':
                    model_name_occurrence += 1
                if key == 'processor':
                    processor_occurrence += 1
                i += 1
            elif key == 'physical id':
                physid = val
                if physid not in sockets:
                    sockets[physid] = 1
            elif key == 'core id':
                coreid = val
                if coreid not in sockets:
                    cores[coreid] = 1
            elif key == 'cpu cores':
                sockets[physid] = int(val)
            elif key == 'siblings':
                cores[coreid] = int(val)
            # S390x classic cpuinfo
            elif key == '# processors':
                zp = int(val)
            elif key == 'max thread id':
                zmt = int(val) + 1
            # SPARC
            elif key == 'ncpus active':
                i = int(val)

        # Skip for platforms without vendor_id/model_name in cpuinfo (e.g ppc64le)
        if vendor_id_occurrence > 0:
            if vendor_id_occurrence == model_name_occurrence:
                i = vendor_id_occurrence

        # The fields for ARM CPUs do not always include 'vendor_id' or 'model name',
        # and sometimes includes both 'processor' and 'Processor'.
        # The fields for Power CPUs include 'processor' and 'cpu'.
        # Always use 'processor' count for ARM and Power systems
        if collected_facts.get('ansible_architecture', '').startswith(('armv', 'aarch', 'ppc')):
            i = processor_occurrence

        if collected_facts.get('ansible_architecture') == 's390x':
            # getting sockets would require 5.7+ with CONFIG_SCHED_TOPOLOGY
            cpu_facts['processor_count'] = 1
            cpu_facts['processor_cores'] = round(zp / zmt)
            cpu_facts['processor_threads_per_core'] = zmt
            cpu_facts['processor_vcpus'] = zp
            cpu_facts['processor_nproc'] = zp
        else:
            if xen_paravirt:
                cpu_facts['processor_count'] = i
                cpu_facts['processor_cores'] = i
                cpu_facts['processor_threads_per_core'] = 1
                cpu_facts['processor_vcpus'] = i
                cpu_facts['processor_nproc'] = i
            else:
                if sockets:
                    cpu_facts['processor_count'] = len(sockets)
                else:
                    cpu_facts['processor_count'] = i

                socket_values = list(sockets.values())
                if socket_values and socket_values[0]:
                    cpu_facts['processor_cores'] = socket_values[0]
                else:
                    cpu_facts['processor_cores'] = 1

                core_values = list(cores.values())
                if core_values:
                    cpu_facts['processor_threads_per_core'] = round(core_values[0] / cpu_facts['processor_cores'])
                else:
                    cpu_facts['processor_threads_per_core'] = round(1 / cpu_facts['processor_cores'])

                cpu_facts['processor_vcpus'] = (cpu_facts['processor_threads_per_core'] *
                                                cpu_facts['processor_count'] * cpu_facts['processor_cores'])

                cpu_facts['processor_nproc'] = processor_occurrence

        # if the number of processors available to the module's
        # thread cannot be determined, the processor count
        # reported by /proc will be the default (as previously defined)
        try:
            cpu_facts['processor_nproc'] = len(
                os.sched_getaffinity(0)
            )
        except AttributeError:
            # In Python < 3.3, os.sched_getaffinity() is not available
            nproc_cmd = self.module.get_bin_path('nproc')
            if nproc_cmd is not None:
                rc, out, _err = self.module.run_command(nproc_cmd)
                if rc == 0:
                    cpu_facts['processor_nproc'] = int(out)

        return cpu_facts