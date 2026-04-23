def test_config_file_command_key(self):
        options = [
            (None, None, None),  # Default case.
            ('--copies', 'symlinks', False),
            ('--without-pip', 'with_pip', False),
            ('--system-site-packages', 'system_site_packages', True),
            ('--clear', 'clear', True),
            ('--upgrade', 'upgrade', True),
            ('--upgrade-deps', 'upgrade_deps', True),
            ('--prompt="foobar"', 'prompt', 'foobar'),
            ('--without-scm-ignore-files', 'scm_ignore_files', frozenset()),
        ]
        for opt, attr, value in options:
            with self.subTest(opt=opt, attr=attr, value=value):
                rmtree(self.env_dir)
                if not attr:
                    kwargs = {}
                else:
                    kwargs = {attr: value}
                b = venv.EnvBuilder(**kwargs)
                b.upgrade_dependencies = Mock() # avoid pip command to upgrade deps
                b._setup_pip = Mock() # avoid pip setup
                self.run_with_capture(b.create, self.env_dir)
                data = self.get_text_file_contents('pyvenv.cfg')
                if not attr or opt.endswith('git'):
                    for opt in ('--system-site-packages', '--clear', '--upgrade',
                                '--upgrade-deps', '--prompt'):
                        self.assertNotRegex(data, rf'command = .* {opt}')
                elif os.name=='nt' and attr=='symlinks':
                    pass
                else:
                    self.assertRegex(data, rf'command = .* {opt}')