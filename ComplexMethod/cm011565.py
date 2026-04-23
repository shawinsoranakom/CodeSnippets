def _try_wait_get(self, b64_keys, override_timeout=None):
        timeout = self.timeout if override_timeout is None else override_timeout  # type: ignore[attr-defined]
        deadline = time.time() + timeout.total_seconds()

        while True:
            # Read whole directory (of keys), filter only the ones waited for
            all_nodes = None
            try:
                all_nodes = self.client.get(key=self.prefix)
                req_nodes = {
                    node.key: node.value
                    for node in all_nodes.children
                    if node.key in b64_keys
                }

                if len(req_nodes) == len(b64_keys):
                    # All keys are available
                    return req_nodes
            except etcd.EtcdKeyNotFound:
                pass

            watch_timeout = deadline - time.time()
            if watch_timeout <= 0:
                return None

            try:
                index = all_nodes.etcd_index + 1 if all_nodes else 0
                self.client.watch(
                    key=self.prefix,
                    recursive=True,
                    timeout=watch_timeout,
                    index=index,
                )
            except etcd.EtcdWatchTimedOut:
                if time.time() >= deadline:
                    return None
                else:
                    continue
            except etcd.EtcdEventIndexCleared:
                continue