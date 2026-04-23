def get_memory_facts(self):
        memory_facts = {
            'memtotal_mb': int(self.sysctl['hw.memsize']) // 1024 // 1024,
            'memfree_mb': 0,
        }

        total_used = 0
        page_size = int(self.sysctl.get('hw.pagesize', 4096))

        vm_stat_command = self.module.get_bin_path('vm_stat')
        if vm_stat_command is None:
            return memory_facts

        if vm_stat_command:
            rc, out, err = self.module.run_command(vm_stat_command)
            if rc == 0:
                # Free = Total - (Wired + active + inactive)
                # Get a generator of tuples from the command output so we can later
                # turn it into a dictionary
                memory_stats = (line.rstrip('.').split(':', 1) for line in out.splitlines())

                # Strip extra left spaces from the value
                memory_stats = dict((k, v.lstrip()) for k, v in memory_stats)

                for k, v in memory_stats.items():
                    try:
                        memory_stats[k] = int(v)
                    except ValueError:
                        # Most values convert cleanly to integer values but if the field does
                        # not convert to an integer, just leave it alone.
                        pass

                if memory_stats.get('Pages wired down'):
                    total_used += memory_stats['Pages wired down'] * page_size
                if memory_stats.get('Pages active'):
                    total_used += memory_stats['Pages active'] * page_size
                if memory_stats.get('Pages inactive'):
                    total_used += memory_stats['Pages inactive'] * page_size

                memory_facts['memfree_mb'] = memory_facts['memtotal_mb'] - (total_used // 1024 // 1024)

        return memory_facts