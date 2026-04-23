def apply_overrides(self, overrides):
        for override in overrides:
            when = override.get('when')
            if when and when not in self and when != self._start:
                logger.debug(f'Ignored {when!r} override')
                continue

            override_hash = override.get('hash') or when
            if override['action'] == 'add':
                commit = Commit(override.get('hash'), override['short'], override.get('authors') or [])
                logger.info(f'ADD    {commit}')
                self._commits_added.append(commit)

            elif override['action'] == 'remove':
                if override_hash in self._commits:
                    logger.info(f'REMOVE {self._commits[override_hash]}')
                    del self._commits[override_hash]

            elif override['action'] == 'change':
                if override_hash not in self._commits:
                    continue
                commit = Commit(override_hash, override['short'], override.get('authors') or [])
                logger.info(f'CHANGE {self._commits[commit.hash]} -> {commit}')
                if match := self.FIXES_RE.search(commit.short):
                    fix_commitish = match.group(1)
                    if fix_commitish in self._commits:
                        del self._commits[commit.hash]
                        self._fixes[fix_commitish].append(commit)
                        logger.info(f'Found fix for {fix_commitish[:HASH_LENGTH]}: {commit.hash[:HASH_LENGTH]}')
                        continue
                self._commits[commit.hash] = commit

        self._commits = dict(reversed(self._commits.items()))