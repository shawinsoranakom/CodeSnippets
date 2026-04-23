def _get_script(self, script_type: ScriptType, /) -> Script:
        skipped_components: list[_SkippedComponent] = []
        for _, from_source in self._iter_script_sources():
            script = from_source(script_type)
            if not script:
                continue
            if isinstance(script, _SkippedComponent):
                skipped_components.append(script)
                continue
            if not self.is_dev:
                # Matching patch version is expected to have same hash
                if version_tuple(script.version, lenient=True)[:2] != version_tuple(self._SCRIPT_VERSION, lenient=True)[:2]:
                    self.logger.warning(
                        f'Challenge solver {script_type.value} script version {script.version} '
                        f'is not supported (source: {script.source.value}, variant: {script.variant}, supported version: {self._SCRIPT_VERSION})')
                    if script.source is ScriptSource.CACHE:
                        self.logger.debug('Clearing outdated cached script')
                        self.ie.cache.store(self._CACHE_SECTION, script_type.value, None)
                    continue
                script_hashes = self._ALLOWED_HASHES[script.type].get(script.variant, [])
                if script_hashes and script.hash not in script_hashes:
                    self.logger.warning(
                        f'Hash mismatch on challenge solver {script.type.value} script '
                        f'(source: {script.source.value}, variant: {script.variant}, hash: {script.hash})!{provider_bug_report_message(self)}')
                    if script.source is ScriptSource.CACHE:
                        self.logger.debug('Clearing invalid cached script')
                        self.ie.cache.store(self._CACHE_SECTION, script_type.value, None)
                    continue
            self.logger.debug(
                f'Using challenge solver {script.type.value} script v{script.version} '
                f'(source: {script.source.value}, variant: {script.variant.value})')
            break

        else:
            self._available = False
            raise JsChallengeProviderRejectedRequest(
                f'No usable challenge solver {script_type.value} script available',
                _skipped_components=skipped_components or None,
            )

        return script