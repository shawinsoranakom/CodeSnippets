def _update_from_database(self, names: Iterable[str]) -> None:
        names = tuple(name for name in names if name in self._modules)
        if not names:
            return
        # update modules with values from the database (if exist)
        query = '''
            SELECT name, id, state, demo, latest_version AS installed_version
            FROM ir_module_module
            WHERE name IN %s
        '''
        self._cr.execute(query, [names])
        for name, id_, state, demo, installed_version in self._cr.fetchall():
            if state == 'uninstallable':
                _logger.warning('module %s: not installable, skipped', name)
                self._remove(name)
                continue
            if self.mode == 'load' and state in ['to install', 'uninstalled']:
                _logger.info('module %s: not installed, skipped', name)
                self._remove(name)
                continue
            if name not in self._modules:
                # has been recursively removed for sake of not installable or not installed
                continue
            module = self._modules[name]
            module.id = id_
            module.state = state
            module.demo = demo
            module.installed_version = installed_version
            module.load_version = installed_version
            module.load_state = state