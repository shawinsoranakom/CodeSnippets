def collect(self, module=None, collected_facts=None):

        rc = -1
        facts_dict = {'system_capabilities_enforced': 'N/A',
                      'system_capabilities': 'N/A'}
        if module:
            capsh_path = module.get_bin_path('capsh')
            if capsh_path:
                # NOTE: -> get_caps_data()/parse_caps_data() for easier mocking -akl
                try:
                    rc, out, err = module.run_command([capsh_path, "--print"], errors='surrogate_then_replace', handle_exceptions=False)
                except OSError as ex:
                    module.error_as_warning('Could not query system capabilities.', exception=ex)

            if rc == 0:
                enforced_caps = []
                enforced = 'NA'
                for line in out.splitlines():
                    if len(line) < 1:
                        continue
                    if line.startswith('Current:'):
                        if line.split(':')[1].strip() == '=ep':
                            enforced = 'False'
                        else:
                            enforced = 'True'
                            enforced_caps = [i.strip() for i in line.split('=')[1].split(',')]

                facts_dict['system_capabilities_enforced'] = enforced
                facts_dict['system_capabilities'] = enforced_caps

        return facts_dict