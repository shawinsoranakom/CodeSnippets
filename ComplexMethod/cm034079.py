def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}

        pkg_mgr_name = self._default_unknown_pkg_mgr
        for pkg in self.pkg_mgrs(collected_facts):
            if os.path.exists(pkg['path']):
                pkg_mgr_name = pkg['name']

        # Handle distro family defaults when more than one package manager is
        # installed or available to the distro, the ansible_fact entry should be
        # the default package manager officially supported by the distro.
        if collected_facts['ansible_os_family'] == "RedHat":
            pkg_mgr_name = self._check_rh_versions()
        elif collected_facts['ansible_os_family'] == 'Debian' and pkg_mgr_name != 'apt':
            # It's possible to install dnf, zypper, rpm, etc inside of
            # Debian. Doing so does not mean the system wants to use them.
            pkg_mgr_name = 'apt'
        elif collected_facts['ansible_os_family'] == 'Altlinux':
            if pkg_mgr_name == 'apt':
                pkg_mgr_name = 'apt_rpm'

        # Check if /usr/bin/apt-get is ordinary (dpkg-based) APT or APT-RPM
        if pkg_mgr_name == 'apt':
            pkg_mgr_name = self._check_apt_flavor(pkg_mgr_name)

        return {'pkg_mgr': pkg_mgr_name}