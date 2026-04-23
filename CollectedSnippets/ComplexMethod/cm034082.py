def parse_distribution_file_SUSE(self, name, data, path, collected_facts):
        suse_facts = {}
        if 'suse' not in data.lower():
            return False, suse_facts  # TODO: remove if tested without this
        if path == '/etc/os-release':
            for line in data.splitlines():
                distribution = re.search("^NAME=(.*)", line)
                if distribution:
                    suse_facts['distribution'] = distribution.group(1).strip('"')
                # example pattern are 13.04 13.0 13
                distribution_version = re.search(r'^VERSION_ID="?([0-9]+\.?[0-9]*)"?', line)
                if distribution_version:
                    suse_facts['distribution_version'] = distribution_version.group(1)
                    suse_facts['distribution_major_version'] = distribution_version.group(1).split('.')[0]
                if 'open' in data.lower():
                    release = re.search(r'^VERSION_ID="?[0-9]+\.?([0-9]*)"?', line)
                    if release:
                        suse_facts['distribution_release'] = release.groups()[0]
                elif 'enterprise' in data.lower() and 'VERSION_ID' in line:
                    # SLES doesn't got funny release names
                    release = re.search(r'^VERSION_ID="?[0-9]+\.?([0-9]*)"?', line)
                    if release.group(1):
                        release = release.group(1)
                    else:
                        release = "0"  # no minor number, so it is the first release
                    suse_facts['distribution_release'] = release
        elif path == '/etc/SuSE-release':
            if 'open' in data.lower():
                data = data.splitlines()
                distdata = get_file_content(path).splitlines()[0]
                suse_facts['distribution'] = distdata.split()[0]
                for line in data:
                    release = re.search('CODENAME *= *([^\n]+)', line)
                    if release:
                        suse_facts['distribution_release'] = release.groups()[0].strip()
            elif 'enterprise' in data.lower():
                lines = data.splitlines()
                distribution = lines[0].split()[0]
                if "Server" in data:
                    suse_facts['distribution'] = "SLES"
                elif "Desktop" in data:
                    suse_facts['distribution'] = "SLED"
                for line in lines:
                    release = re.search('PATCHLEVEL = ([0-9]+)', line)  # SLES doesn't got funny release names
                    if release:
                        suse_facts['distribution_release'] = release.group(1)
                        suse_facts['distribution_version'] = collected_facts['distribution_version'] + '.' + release.group(1)

        # Check VARIANT_ID first for SLES4SAP or SL-Micro
        variant_id_match = re.search(r'^VARIANT_ID="?([^"\n]*)"?', data, re.MULTILINE)
        if variant_id_match:
            variant_id = variant_id_match.group(1)
            if variant_id in ('server-sap', 'sles-sap'):
                suse_facts['distribution'] = 'SLES_SAP'
            elif variant_id == 'transactional':
                suse_facts['distribution'] = 'SL-Micro'
        else:
            # Fallback for older SLES 15 using baseproduct symlink
            if os.path.islink('/etc/products.d/baseproduct'):
                resolved = os.path.realpath('/etc/products.d/baseproduct')
                if resolved.endswith('SLES_SAP.prod'):
                    suse_facts['distribution'] = 'SLES_SAP'
                elif resolved.endswith('SL-Micro.prod'):
                    suse_facts['distribution'] = 'SL-Micro'

        return True, suse_facts