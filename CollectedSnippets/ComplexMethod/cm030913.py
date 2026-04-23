def check_config(self, configs, expected):
        config = dict(configs['config'])
        if MS_WINDOWS:
            value = config.get(key := 'program_name')
            if value and isinstance(value, str):
                value = value[:len(value.lower().removesuffix('.exe'))]
                if debug_build(sys.executable):
                    value = value[:len(value.lower().removesuffix('_d'))]
                config[key] = value
        for key, value in list(expected.items()):
            if value is self.IGNORE_CONFIG:
                config.pop(key, None)
                del expected[key]
            # Resolve bool/int mismatches to reduce noise in diffs
            if isinstance(value, (bool, int)) and isinstance(config.get(key), (bool, int)):
                expected[key] = type(config[key])(expected[key])
        self.assertEqual(config, expected)