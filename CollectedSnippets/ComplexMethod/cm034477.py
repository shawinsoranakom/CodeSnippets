def _list_from_unit_files(self, systemctl_path, services):

        # now try unit files for complete picture and final 'status'
        rc, stdout, stderr = self.module.run_command("%s list-unit-files --no-pager --type service --all" % systemctl_path, use_unsafe_shell=True)
        if rc != 0:
            self.module.warn("Could not get unit files data from systemd: %s" % stderr)
        else:
            for line in [svc_line for svc_line in stdout.split('\n') if '.service' in svc_line]:
                # there is one more column (VENDOR PRESET) from `systemctl list-unit-files` for systemd >= 245
                try:
                    service_name, status_val = line.split()[:2]
                except IndexError:
                    self.module.fail_json(msg="Malformed output discovered from systemd list-unit-files: {0}".format(line))
                if service_name not in services:
                    rc, stdout, stderr = self.module.run_command("%s show %s --property=ActiveState" % (systemctl_path, service_name), use_unsafe_shell=True)
                    state = 'unknown'
                    if not rc and stdout != '':
                        state = stdout.replace('ActiveState=', '').rstrip()
                    services[service_name] = {"name": service_name, "state": state, "status": status_val, "source": "systemd"}
                elif services[service_name]["status"] not in self.BAD_STATES:
                    services[service_name]["status"] = status_val