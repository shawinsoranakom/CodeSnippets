def teardown(self) -> None:
        """Perform teardown for code coverage."""
        with tempfile.TemporaryDirectory() as local_temp_path:
            variables = self.get_playbook_variables()
            variables.update(
                local_temp_path=local_temp_path,
            )

            self.run_playbook('windows_coverage_teardown.yml', variables)

            for filename in os.listdir(local_temp_path):
                if all(isinstance(profile.config, WindowsRemoteConfig) for profile in self.profiles):
                    prefix = 'remote'
                elif all(isinstance(profile.config, WindowsInventoryConfig) for profile in self.profiles):
                    prefix = 'inventory'
                else:
                    raise NotImplementedError()

                platform = f'{prefix}-{sanitize_host_name(os.path.splitext(filename)[0])}'

                with zipfile.ZipFile(os.path.join(local_temp_path, filename)) as coverage_zip:
                    for item in coverage_zip.infolist():
                        if item.is_dir():
                            raise Exception(f'Unexpected directory in zip file: {item.filename}')

                        item.filename = update_coverage_filename(item.filename, platform)

                        coverage_zip.extract(item, ResultType.COVERAGE.path)