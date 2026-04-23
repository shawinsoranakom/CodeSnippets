def _lsb_release_bin(self, lsb_path, module):
        lsb_facts = {}

        if not lsb_path:
            return lsb_facts

        rc, out, err = module.run_command([lsb_path, "-a"], errors='surrogate_then_replace')
        if rc != 0:
            return lsb_facts

        for line in out.splitlines():
            if len(line) < 1 or ':' not in line:
                continue
            value = line.split(':', 1)[1].strip()

            if 'LSB Version:' in line:
                lsb_facts['release'] = value
            elif 'Distributor ID:' in line:
                lsb_facts['id'] = value
            elif 'Description:' in line:
                lsb_facts['description'] = value
            elif 'Release:' in line:
                lsb_facts['release'] = value
            elif 'Codename:' in line:
                lsb_facts['codename'] = value

        return lsb_facts