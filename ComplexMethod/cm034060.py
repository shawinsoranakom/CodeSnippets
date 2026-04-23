def get_mount_facts(self):
        mount_facts = {}

        mount_facts['mounts'] = []

        mounts = []

        # AIX does not have mtab but mount command is only source of info (or to use
        # api calls to get same info)
        mount_path = self.module.get_bin_path('mount')
        if mount_path:
            rc, mount_out, err = self.module.run_command(mount_path)
            if mount_out:
                for line in mount_out.split('\n'):
                    fields = line.split()
                    if len(fields) != 0 and fields[0] != 'node' and fields[0][0] != '-' and re.match('^/.*|^[a-zA-Z].*|^[0-9].*', fields[0]):
                        if re.match('^/', fields[0]):
                            # normal mount
                            mount = fields[1]
                            mount_info = {'mount': mount,
                                          'device': fields[0],
                                          'fstype': fields[2],
                                          'options': fields[6],
                                          'time': '%s %s %s' % (fields[3], fields[4], fields[5])}
                            mount_info.update(get_mount_size(mount))
                        else:
                            # nfs or cifs based mount
                            # in case of nfs if no mount options are provided on command line
                            # add into fields empty string...
                            if len(fields) < 8:
                                fields.append("")

                            mount_info = {'mount': fields[2],
                                          'device': '%s:%s' % (fields[0], fields[1]),
                                          'fstype': fields[3],
                                          'options': fields[7],
                                          'time': '%s %s %s' % (fields[4], fields[5], fields[6])}

                        mounts.append(mount_info)

        mount_facts['mounts'] = mounts

        return mount_facts