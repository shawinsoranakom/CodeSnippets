def get_mount_facts(self):

        mounts = []

        # gather system lists
        bind_mounts = self._find_bind_mounts()
        uuids = self._lsblk_uuid()
        mtab_entries = self._mtab_entries()

        # start threads to query each mount
        results = {}
        executor = _futures.DaemonThreadPoolExecutor()
        maxtime = timeout.GATHER_TIMEOUT or timeout.DEFAULT_GATHER_TIMEOUT
        for fields in mtab_entries:
            # Transform octal escape sequences
            fields = [self._replace_octal_escapes(field) for field in fields]

            device, mount, fstype, options = fields[0], fields[1], fields[2], fields[3]
            dump, passno = int(fields[4]), int(fields[5])

            if not device.startswith(('/', '\\')) and ':/' not in device or fstype == 'none':
                continue

            mount_info = {'mount': mount,
                          'device': device,
                          'fstype': fstype,
                          'options': options,
                          'dump': dump,
                          'passno': passno}

            if mount in bind_mounts:
                # only add if not already there, we might have a plain /etc/mtab
                if not self.MTAB_BIND_MOUNT_RE.match(options):
                    mount_info['options'] += ",bind"

            results[mount] = {'info': mount_info, 'timelimit': time.monotonic() + maxtime}
            results[mount]['extra'] = executor.submit(self.get_mount_info, mount, device, uuids)

        # done with spawning new workers, start gc
        executor.shutdown()

        while results:  # wait for workers and get results
            for mount in list(results):
                done = False
                res = results[mount]['extra']
                try:
                    if res.done():
                        done = True
                        if res.exception() is None:
                            mount_size, uuid = res.result()
                            if mount_size:
                                results[mount]['info'].update(mount_size)
                            results[mount]['info']['uuid'] = uuid or 'N/A'
                        else:
                            # failed, try to find out why, if 'res.successful' we know there are no exceptions
                            results[mount]['info']['note'] = f'Could not get extra information: {res.exception()}'

                    elif time.monotonic() > results[mount]['timelimit']:
                        done = True
                        self.module.warn("Timeout exceeded when getting mount info for %s" % mount)
                        results[mount]['info']['note'] = 'Could not get extra information due to timeout'
                except Exception as e:
                    import traceback
                    done = True
                    results[mount]['info'] = 'N/A'
                    self.module.warn("Error prevented getting extra info for mount %s: [%s] %s." % (mount, type(e), to_text(e)))
                    self.module.debug(traceback.format_exc())

                if done:
                    # move results outside and make loop only handle pending
                    mounts.append(results[mount]['info'])
                    del results[mount]

            # avoid cpu churn, sleep between retrying for loop with remaining mounts
            time.sleep(0.1)

        return {'mounts': mounts}