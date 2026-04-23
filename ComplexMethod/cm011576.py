def load_extra_data(self, rdzv_version, key, timeout=None):
        # 'extra_data' node itself, and the directory it is located in:
        node = self.get_path(f"/rdzv/v_{rdzv_version}/extra_data")
        node_dir = self.get_path(f"/rdzv/v_{rdzv_version}")

        # TODO: implement timeout
        # https://github.com/pytorch/elastic/issues/12
        while True:
            # Combined wait for the node itself, and the key inside it.
            root = self.client.get(node_dir)

            # Find the extra_data node, if it exists
            extra_data = [n for n in root.children if n.key == node]
            if len(extra_data) > 1:
                raise AssertionError

            # Node for extra_data exists, check the desired key inside it.
            if len(extra_data) == 1:
                extra_data_dict = json.loads(extra_data[0].value)
                if key in extra_data_dict:
                    return extra_data_dict[key]

            # The 'extra_data' node doesn't exist, or they key isn't published yet.
            # Wait for interesting events on the extra_data node and retry.
            try:
                self.client.watch(node, index=root.etcd_index + 1)
            except (etcd.EtcdEventIndexCleared, etcd.EtcdWatchTimedOut):
                pass