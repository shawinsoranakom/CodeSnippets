def _list_from_units(self, systemctl_path, services):

        # list units as systemd sees them
        rc, stdout, stderr = self.module.run_command("%s list-units --no-pager --type service --all --plain" % systemctl_path, use_unsafe_shell=True)
        if rc != 0:
            self.module.warn("Could not list units from systemd: %s" % stderr)
        else:
            for line in [svc_line for svc_line in stdout.split('\n') if '.service' in svc_line]:

                state_val = "stopped"
                status_val = "unknown"
                fields = line.split()

                # systemd sometimes gives misleading status
                # check all fields for bad states
                for bad in self.BAD_STATES:
                    # except description
                    if bad in fields[:-1]:
                        status_val = bad
                        break
                else:
                    # active/inactive
                    status_val = fields[2]

                service_name = fields[0]
                if fields[3] == "running":
                    state_val = "running"

                services[service_name] = {"name": service_name, "state": state_val, "status": status_val, "source": "systemd"}