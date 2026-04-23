def get_lvm_facts(self):
        """ Get LVM Facts if running as root and lvm utils are available """

        lvm_facts = {'lvm': 'N/A'}
        vgs_cmd = self.module.get_bin_path('vgs')
        if vgs_cmd is None:
            return lvm_facts

        if os.getuid() == 0:
            lvm_util_options = '--noheadings --nosuffix --units g --separator ,'

            # vgs fields: VG #PV #LV #SN Attr VSize VFree
            vgs = {}
            rc, vg_lines, err = self.module.run_command('%s %s' % (vgs_cmd, lvm_util_options))
            for vg_line in vg_lines.splitlines():
                items = vg_line.strip().split(',')
                vgs[items[0]] = {
                    'size_g': items[-2],
                    'free_g': items[-1],
                    'num_lvs': items[2],
                    'num_pvs': items[1],
                    'lvs': {},
                }

            lvs_path = self.module.get_bin_path('lvs')
            # lvs fields:
            # LV VG Attr LSize Pool Origin Data% Move Log Copy% Convert
            lvs = {}
            if lvs_path:
                rc, lv_lines, err = self.module.run_command('%s %s' % (lvs_path, lvm_util_options))
                for lv_line in lv_lines.splitlines():
                    items = lv_line.strip().split(',')
                    vg_name = items[1]
                    lv_name = items[0]
                    # The LV name is only unique per VG, so the top level fact lvs can be misleading.
                    # TODO: deprecate lvs in favor of vgs
                    lvs[lv_name] = {'size_g': items[3], 'vg': vg_name}
                    try:
                        vgs[vg_name]['lvs'][lv_name] = {'size_g': items[3]}
                    except KeyError:
                        self.module.warn(
                            "An LVM volume group was created while gathering LVM facts, "
                            "and is not included in ansible_facts['vgs']."
                        )

            pvs_path = self.module.get_bin_path('pvs')
            # pvs fields: PV VG #Fmt #Attr PSize PFree
            pvs = {}
            if pvs_path:
                rc, pv_lines, err = self.module.run_command('%s %s' % (pvs_path, lvm_util_options))
                for pv_line in pv_lines.splitlines():
                    items = pv_line.strip().split(',')
                    pvs[self._find_mapper_device_name(items[0])] = {
                        'size_g': items[4],
                        'free_g': items[5],
                        'vg': items[1]}

            lvm_facts['lvm'] = {'lvs': lvs, 'vgs': vgs, 'pvs': pvs}

        return lvm_facts