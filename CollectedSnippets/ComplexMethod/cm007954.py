def groups(self):
        group_dict = defaultdict(list)
        for commit in self:
            upstream_re = self.UPSTREAM_MERGE_RE.search(commit.short)
            if upstream_re:
                commit.short = f'[upstream] Merged with youtube-dl {upstream_re.group(1)}'

            match = self.MESSAGE_RE.fullmatch(commit.short)
            if not match:
                logger.error(f'Error parsing short commit message: {commit.short!r}')
                continue

            prefix, sub_details_alt, message, issues = match.groups()
            issues = [issue.strip()[1:] for issue in issues.split(',')] if issues else []

            if prefix:
                groups, details, sub_details = zip(*map(self.details_from_prefix, prefix.split(',')), strict=True)
                group = next(iter(filter(None, groups)), None)
                details = ', '.join(unique(details))
                sub_details = list(itertools.chain.from_iterable(sub_details))
            else:
                group = CommitGroup.CORE
                details = None
                sub_details = []

            if sub_details_alt:
                sub_details.append(sub_details_alt)
            sub_details = tuple(unique(sub_details))

            if not group:
                if self.EXTRACTOR_INDICATOR_RE.search(commit.short):
                    group = CommitGroup.EXTRACTOR
                    logger.error(f'Assuming [ie] group for {commit.short!r}')
                else:
                    group = CommitGroup.CORE

            commit_info = CommitInfo(
                details, sub_details, message.strip(),
                issues, commit, self._fixes[commit.hash])

            logger.debug(f'Resolved {commit.short!r} to {commit_info!r}')
            group_dict[group].append(commit_info)

        return group_dict