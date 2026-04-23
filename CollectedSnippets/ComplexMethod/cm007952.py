def _get_commits_and_fixes(self, default_author):
        result = run_process(
            self.COMMAND, 'log', f'--format=%H%n%s%n%b%n{self.COMMIT_SEPARATOR}',
            f'{self._start}..{self._end}' if self._start else self._end).stdout

        commits, reverts = {}, {}
        fixes = defaultdict(list)
        lines = iter(result.splitlines(False))
        for i, commit_hash in enumerate(lines):
            short = next(lines)
            skip = short.startswith('Release ') or short == '[version] update'

            fix_commitish = None
            if match := self.FIXES_RE.search(short):
                fix_commitish = match.group(1)

            authors = [default_author] if default_author else []
            for line in iter(lambda: next(lines), self.COMMIT_SEPARATOR):
                if match := self.AUTHOR_INDICATOR_RE.match(line):
                    authors = sorted(map(str.strip, line[match.end():].split(',')), key=str.casefold)
                if not fix_commitish and (match := self.FIXES_RE.fullmatch(line)):
                    fix_commitish = match.group(1)

            commit = Commit(commit_hash, short, authors)
            if skip and (self._start or not i):
                logger.debug(f'Skipped commit: {commit}')
                continue
            elif skip:
                logger.debug(f'Reached Release commit, breaking: {commit}')
                break

            if match := self.REVERT_RE.fullmatch(commit.short):
                reverts[match.group(1)] = commit
                continue

            if fix_commitish:
                fixes[fix_commitish].append(commit)

            commits[commit.hash] = commit

        for commitish, revert_commit in reverts.items():
            if reverted := commits.pop(commitish, None):
                logger.debug(f'{commitish} fully reverted {reverted}')
            else:
                commits[revert_commit.hash] = revert_commit

        for commitish, fix_commits in fixes.items():
            if commitish in commits:
                hashes = ', '.join(commit.hash[:HASH_LENGTH] for commit in fix_commits)
                logger.info(f'Found fix(es) for {commitish[:HASH_LENGTH]}: {hashes}')
                for fix_commit in fix_commits:
                    del commits[fix_commit.hash]
            else:
                logger.debug(f'Commit with fixes not in changes: {commitish[:HASH_LENGTH]}')

        return commits, fixes