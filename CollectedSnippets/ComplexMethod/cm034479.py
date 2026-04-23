def gather_services(self):

        services = {}
        self.rcctl_path = self.module.get_bin_path("rcctl")
        if self.rcctl_path:

            # populate services will all possible
            for svc in self.query_rcctl('all'):
                services[svc] = {'name': svc, 'source': 'rcctl', 'rogue': False}
                services[svc].update(self.get_info(svc))

            for svc in self.query_rcctl('on'):
                services[svc].update({'status': 'enabled'})

            for svc in self.query_rcctl('started'):
                services[svc].update({'state': 'running'})

            # Override the state for services which are marked as 'failed'
            for svc in self.query_rcctl('failed'):
                services[svc].update({'state': 'failed'})

            for svc in services.keys():
                # Based on the list of services that are enabled/failed, determine which are disabled
                if services[svc].get('status') is None:
                    services[svc].update({'status': 'disabled'})

                # and do the same for those are aren't running
                if services[svc].get('state') is None:
                    services[svc].update({'state': 'stopped'})

            for svc in self.query_rcctl('rogue'):
                services[svc]['rogue'] = True

        return services