def get_service_tools(self):

        paths = ['/sbin', '/usr/sbin', '/bin', '/usr/bin']
        binaries = ['service', 'chkconfig', 'update-rc.d', 'rc-service', 'rc-update', 'initctl', 'systemctl', 'start', 'stop', 'restart', 'insserv']
        initpaths = ['/etc/init.d']
        location = dict()

        for binary in binaries:
            location[binary] = self.module.get_bin_path(binary, opt_dirs=paths)

        for initdir in initpaths:
            initscript = "%s/%s" % (initdir, self.name)
            if os.path.isfile(initscript):
                self.svc_initscript = initscript

        def check_systemd():

            # tools must be installed
            if location.get('systemctl', False):
                return is_systemd_managed(self.module)
            return False

        # Locate a tool to enable/disable a service
        if check_systemd():
            # service is managed by systemd
            self.__systemd_unit = self.name
            self.svc_cmd = location['systemctl']
            self.enable_cmd = location['systemctl']

        elif location.get('initctl', False) and os.path.exists("/etc/init/%s.conf" % self.name):
            # service is managed by upstart
            self.enable_cmd = location['initctl']
            # set the upstart version based on the output of 'initctl version'
            self.upstart_version = LooseVersion('0.0.0')
            try:
                version_re = re.compile(r'\(upstart (.*)\)')
                rc, stdout, stderr = self.module.run_command('%s version' % location['initctl'])
                if rc == 0:
                    res = version_re.search(stdout)
                    if res:
                        self.upstart_version = LooseVersion(res.groups()[0])
            except Exception:
                pass  # we'll use the default of 0.0.0

            self.svc_cmd = location['initctl']

        elif location.get('rc-service', False):
            # service is managed by OpenRC
            self.svc_cmd = location['rc-service']
            self.enable_cmd = location['rc-update']
            return  # already have service start/stop tool too!

        elif self.svc_initscript:
            # service is managed by with SysV init scripts
            if location.get('update-rc.d', False):
                # and uses update-rc.d
                self.enable_cmd = location['update-rc.d']
            elif location.get('insserv', None):
                # and uses insserv
                self.enable_cmd = location['insserv']
            elif location.get('chkconfig', False):
                # and uses chkconfig
                self.enable_cmd = location['chkconfig']

        if self.enable_cmd is None:
            fail_if_missing(self.module, False, self.name, msg='host')

        # If no service control tool selected yet, try to see if 'service' is available
        if self.svc_cmd is None and location.get('service', False):
            self.svc_cmd = location['service']

        # couldn't find anything yet
        if self.svc_cmd is None and not self.svc_initscript:
            self.module.fail_json(msg='cannot find \'service\' binary or init script for service,  possible typo in service name?, aborting')

        if location.get('initctl', False):
            self.svc_initctl = location['initctl']