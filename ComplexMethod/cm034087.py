def get_virtual_facts(self):
        virtual_facts = {}
        host_tech = set()
        guest_tech = set()

        # Set empty values as default
        virtual_facts['virtualization_type'] = ''
        virtual_facts['virtualization_role'] = ''

        if os.path.exists('/dev/xen/xenstore'):
            guest_tech.add('xen')
            virtual_facts['virtualization_type'] = 'xen'
            virtual_facts['virtualization_role'] = 'guest'

        kern_vm_guest = self.detect_virt_product('kern.vm_guest')
        guest_tech.update(kern_vm_guest['virtualization_tech_guest'])
        host_tech.update(kern_vm_guest['virtualization_tech_host'])

        hw_hv_vendor = self.detect_virt_product('hw.hv_vendor')
        guest_tech.update(hw_hv_vendor['virtualization_tech_guest'])
        host_tech.update(hw_hv_vendor['virtualization_tech_host'])

        sec_jail_jailed = self.detect_virt_product('security.jail.jailed')
        guest_tech.update(sec_jail_jailed['virtualization_tech_guest'])
        host_tech.update(sec_jail_jailed['virtualization_tech_host'])

        if virtual_facts['virtualization_type'] == '':
            # We call update here, then re-set virtualization_tech_host/guest
            # later.
            for sysctl in [kern_vm_guest, hw_hv_vendor, sec_jail_jailed]:
                if sysctl:
                    virtual_facts.update(sysctl)

        virtual_vendor_facts = self.detect_virt_vendor('hw.model')
        guest_tech.update(virtual_vendor_facts['virtualization_tech_guest'])
        host_tech.update(virtual_vendor_facts['virtualization_tech_host'])

        if virtual_facts['virtualization_type'] == '':
            virtual_facts.update(virtual_vendor_facts)

        # if vmm.ko kernel module is loaded
        kldstat_bin = self.module.get_bin_path('kldstat')

        if kldstat_bin is not None:
            (rc, out, err) = self.module.run_command('%s -q -m vmm' % kldstat_bin)
            if rc == 0:
                host_tech.add('bhyve')
                virtual_facts['virtualization_type'] = 'bhyve'
                virtual_facts['virtualization_role'] = 'host'

        virtual_facts['virtualization_tech_guest'] = guest_tech
        virtual_facts['virtualization_tech_host'] = host_tech
        return virtual_facts