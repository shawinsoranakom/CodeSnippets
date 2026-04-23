def _format_group(self, group):
        sorted_group = sorted(group, key=CommitInfo.key)
        detail_groups = itertools.groupby(sorted_group, lambda item: (item.details or '').lower())
        for _, items in detail_groups:
            items = list(items)
            details = items[0].details

            if details == 'cleanup':
                items = self._prepare_cleanup_misc_items(items)

            prefix = '-'
            if details:
                if len(items) == 1:
                    prefix = f'- **{details}**:'
                else:
                    yield f'- **{details}**'
                    prefix = '\t-'

            sub_detail_groups = itertools.groupby(items, lambda item: tuple(map(str.lower, item.sub_details)))
            for sub_details, entries in sub_detail_groups:
                if not sub_details:
                    for entry in entries:
                        yield f'{prefix} {self.format_single_change(entry)}'
                    continue

                entries = list(entries)
                sub_prefix = f'{prefix} {", ".join(entries[0].sub_details)}'
                if len(entries) == 1:
                    yield f'{sub_prefix}: {self.format_single_change(entries[0])}'
                    continue

                yield sub_prefix
                for entry in entries:
                    yield f'\t{prefix} {self.format_single_change(entry)}'