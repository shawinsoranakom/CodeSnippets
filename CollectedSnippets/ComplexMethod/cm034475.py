def gather_services(self):
        services = {}

        # find cli tools if available
        self.service_path = self.module.get_bin_path("service")
        self.chkconfig_path = self.module.get_bin_path("chkconfig")
        self.initctl_path = self.module.get_bin_path("initctl")
        self.rc_status_path = self.module.get_bin_path("rc-status")
        self.rc_update_path = self.module.get_bin_path("rc-update")

        if self.service_path and self.chkconfig_path is None and self.rc_status_path is None:
            self._list_sysvinit(services)

        # TODO: review conditionals ... they should not be this 'exclusive'
        if self.initctl_path and self.chkconfig_path is None:
            self._list_upstart(services)
        elif self.chkconfig_path:
            self._list_rh(services)
        elif self.rc_status_path is not None and self.rc_update_path is not None:
            self._list_openrc(services)

        return services