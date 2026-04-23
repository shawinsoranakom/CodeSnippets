def filter_remote_targets(targets: list[TestTarget]) -> list[TestTarget]:
        """Return a filtered list of the given targets, including only those that require support for remote-only Python versions."""
        targets = [target for target in targets if (
            is_subdir(target.path, data_context().content.module_path) or
            is_subdir(target.path, data_context().content.module_utils_path) or
            is_subdir(target.path, data_context().content.unit_module_path) or
            is_subdir(target.path, data_context().content.unit_module_utils_path) or
            # include modules/module_utils within integration test library directories
            re.search('^%s/.*/library/' % re.escape(data_context().content.integration_targets_path), target.path) or
            # special handling for content in ansible-core
            (data_context().content.is_ansible and (
                # utility code that runs in target environments and requires support for remote-only Python versions
                is_subdir(target.path, 'test/lib/ansible_test/_util/target/') or
                # integration test support modules/module_utils continue to require support for remote-only Python versions
                re.search('^test/support/integration/.*/(modules|module_utils)/', target.path) or
                # collection loader requires support for remote-only Python versions
                re.search('^lib/ansible/utils/collection_loader/', target.path)
            ))
        )]

        return targets