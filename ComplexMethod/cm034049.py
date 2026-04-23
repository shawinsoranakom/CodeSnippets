def get_ethtool_data(self, device):

        data = {}
        ethtool_path = self.module.get_bin_path("ethtool")
        # FIXME: exit early on falsey ethtool_path and un-indent
        if ethtool_path:
            args = [ethtool_path, '-k', device]
            rc, stdout, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            # FIXME: exit early on falsey if we can
            if rc == 0:
                features = {}
                for line in stdout.strip().splitlines():
                    if not line or line.endswith(":"):
                        continue
                    key, value = line.split(": ")
                    if not value:
                        continue
                    features[key.strip().replace('-', '_')] = value.strip()
                data['features'] = features

            args = [ethtool_path, '-T', device]
            rc, stdout, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                data['timestamping'] = [m.lower() for m in re.findall(r'SOF_TIMESTAMPING_(\w+)', stdout)]
                data['hw_timestamp_filters'] = [m.lower() for m in re.findall(r'HWTSTAMP_FILTER_(\w+)', stdout)]
                m = re.search(r'PTP Hardware Clock: (\d+)', stdout)
                if m:
                    data['phc_index'] = int(m.groups()[0])

        return data