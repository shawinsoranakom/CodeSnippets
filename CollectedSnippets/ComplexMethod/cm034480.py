def get_info(self, service):

        service_info = {'status': 'unknown'}
        rc, stdout, stderr = self.module.run_command("%s %s describe" % (self.service, service))
        if rc == 0:
            service_info['description'] = stdout
            rc, stdout, stderr = self.module.run_command("%s %s status" % (self.service, service))
            if rc == 0:
                service_info['status'] = 'running'
                p = re.compile(r'^\s?%s is running as pid (\d+).' % service)
                matches = p.match(stdout[0])
                if matches:
                    # does not always get pid output
                    service_info['pid'] = matches[0]
                else:
                    service_info['pid'] = 'N/A'
            elif rc == 1:
                if stdout and 'is not running' in stdout.splitlines()[0]:
                    service_info['status'] = 'stopped'
                elif stderr and 'unknown directive' in stderr.splitlines()[0]:
                    service_info['status'] = 'unknown'
                    self.module.warn('Status query not supported for %s' % service)
                else:
                    service_info['status'] = 'unknown'
                    out = stderr if stderr else stdout
                    self.module.warn('Could not retrieve status for %s: %s' % (service, out))
        else:
            out = stderr if stderr else stdout
            self.module.warn("Failed to get info for %s, no system message (rc=%s): %s" % (service, rc, out))

        return service_info