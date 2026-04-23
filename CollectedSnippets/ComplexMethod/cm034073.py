def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        lsb_facts = {}

        if not module:
            return facts_dict

        lsb_path = module.get_bin_path('lsb_release')

        # try the 'lsb_release' script first
        if lsb_path:
            lsb_facts = self._lsb_release_bin(lsb_path,
                                              module=module)

        # no lsb_release, try looking in /etc/lsb-release
        if not lsb_facts:
            lsb_facts = self._lsb_release_file('/etc/lsb-release')

        if lsb_facts and 'release' in lsb_facts:
            lsb_facts['major_release'] = lsb_facts['release'].split('.')[0]

        for k, v in lsb_facts.items():
            if v:
                lsb_facts[k] = v.strip(LSBFactCollector.STRIP_QUOTES)

        facts_dict['lsb'] = lsb_facts
        return facts_dict