def collect(self, module=None, collected_facts=None):
        facts_dict = {}

        if not module:
            return facts_dict

        collected_facts = collected_facts or {}
        service_mgr_name = None

        # TODO: detect more custom init setups like bootscripts, dmd, s6, Epoch, etc
        # also other OSs other than linux might need to check across several possible candidates

        # Mapping of proc_1 values to more useful names
        proc_1_map = {
            'procd': 'openwrt_init',
            'runit-init': 'runit',
            'svscan': 'svc',
            'openrc-init': 'openrc',
        }

        # try various forms of querying pid 1
        proc_1 = get_file_content('/proc/1/comm')
        if proc_1 is None:
            rc, proc_1, err = module.run_command("ps -p 1 -o comm|tail -n 1", use_unsafe_shell=True)

            # if command fails, or stdout is empty string or the output of the command starts with what looks like a PID,
            # then the 'ps' command probably didn't work the way we wanted, probably because it's busybox
            if rc != 0 or not proc_1.strip() or re.match(r' *[0-9]+ ', proc_1):
                proc_1 = None

        # The ps command above may return "COMMAND" if the user cannot read /proc, e.g. with grsecurity
        if proc_1 == "COMMAND\n":
            proc_1 = None

        if proc_1 is None and os.path.islink('/sbin/init'):
            proc_1 = os.readlink('/sbin/init')

        if proc_1 is not None:
            proc_1 = os.path.basename(proc_1)
            proc_1 = to_native(proc_1)
            proc_1 = proc_1.strip()

        if proc_1 is not None and (proc_1 == 'init' or proc_1.endswith('sh')):
            # many systems return init, so this cannot be trusted, if it ends in 'sh' it probably is a shell in a container
            proc_1 = None

        # if not init/None it should be an identifiable or custom init, so we are done!
        if proc_1 is not None:
            # Lookup proc_1 value in map and use proc_1 value itself if no match
            service_mgr_name = proc_1_map.get(proc_1, proc_1)

        # start with the easy ones
        elif collected_facts.get('ansible_distribution', None) == 'MacOSX':
            # FIXME: find way to query executable, version matching is not ideal
            if LooseVersion(platform.mac_ver()[0]) >= LooseVersion('10.4'):
                service_mgr_name = 'launchd'
            else:
                service_mgr_name = 'systemstarter'
        elif 'BSD' in collected_facts.get('ansible_system', '') or collected_facts.get('ansible_system') in ['Bitrig', 'DragonFly']:
            # FIXME: we might want to break out to individual BSDs or 'rc'
            service_mgr_name = 'bsdinit'
        elif collected_facts.get('ansible_system') == 'AIX':
            service_mgr_name = 'src'
        elif collected_facts.get('ansible_system') == 'SunOS':
            service_mgr_name = 'smf'
        elif collected_facts.get('ansible_distribution') == 'OpenWrt':
            service_mgr_name = 'openwrt_init'
        elif collected_facts.get('ansible_distribution') == 'SMGL':
            service_mgr_name = 'simpleinit_msb'
        elif collected_facts.get('ansible_system') == 'Linux':
            # FIXME: mv is_systemd_managed
            if self.is_systemd_managed(module=module):
                service_mgr_name = 'systemd'
            elif module.get_bin_path('initctl') and os.path.exists("/etc/init/"):
                service_mgr_name = 'upstart'
            elif os.path.exists('/sbin/openrc'):
                service_mgr_name = 'openrc'
            elif self.is_systemd_managed_offline(module=module):
                service_mgr_name = 'systemd'
            elif os.path.exists('/etc/init.d/'):
                service_mgr_name = 'sysvinit'
            elif os.path.exists('/etc/dinit.d/'):
                service_mgr_name = 'dinit'

        if not service_mgr_name:
            # if we cannot detect, fallback to generic 'service'
            service_mgr_name = 'service'

        facts_dict['service_mgr'] = service_mgr_name
        return facts_dict