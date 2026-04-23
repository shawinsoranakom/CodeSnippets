def _list_openrc(self, services):
        all_services_runlevels = {}
        dummy, stdout, dummy = self.module.run_command("%s -a -s -m 2>&1 | grep '^ ' | tr -d '[]'" % self.rc_status_path, use_unsafe_shell=True)
        dummy, stdout_u, dummy = self.module.run_command("%s show -v 2>&1 | grep '|'" % self.rc_update_path, use_unsafe_shell=True)
        for line in stdout_u.split('\n'):
            line_data = line.split('|')
            if len(line_data) < 2:
                continue
            service_name = line_data[0].strip()
            runlevels = line_data[1].strip()
            if not runlevels:
                all_services_runlevels[service_name] = None
            else:
                all_services_runlevels[service_name] = runlevels.split()
        for line in stdout.split('\n'):
            line_data = line.split()
            if len(line_data) < 2:
                continue
            service_name = line_data[0]
            # Skip lines which are not service names
            if service_name == "*":
                continue
            service_state = line_data[1]
            try:
                service_runlevels = all_services_runlevels[service_name]
            except KeyError:
                self.module.warn(f"Service {service_name} not found in the service list")
                continue
            service_data = {"name": service_name, "runlevels": service_runlevels, "state": service_state, "source": "openrc"}
            services[service_name] = service_data