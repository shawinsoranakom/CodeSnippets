def __report_skipped_components(self, components: list[_SkippedComponent], /):
        runtime_components = collections.defaultdict(list)
        for component in components:
            runtime_components[component.component].append(component.runtime)
        for runtimes in runtime_components.values():
            runtimes.sort()

        description_lookup = {
            'ejs:npm': 'NPM package',
            'ejs:github': 'challenge solver script',
        }

        descriptions = [
            f'{description_lookup.get(component, component)} ({", ".join(runtimes)})'
            for component, runtimes in runtime_components.items()
            if runtimes
        ]
        flags = [
            f' --remote-components {f"{component}  (recommended)" if component == "ejs:github" else f"{component} "}'
            for component, runtimes in runtime_components.items()
            if runtimes
        ]

        def join_parts(parts, joiner):
            if not parts:
                return ''
            if len(parts) == 1:
                return parts[0]
            return f'{", ".join(parts[:-1])} {joiner} {parts[-1]}'

        if len(descriptions) == 1:
            msg = (
                f'Remote component {descriptions[0]} was skipped. '
                f'It may be required to solve JS challenges. '
                f'You can enable the download with {flags[0]}')
        else:
            msg = (
                f'Remote components {join_parts(descriptions, "and")} were skipped. '
                f'These may be required to solve JS challenges. '
                f'You can enable these downloads with {join_parts(flags, "or")}, respectively')

        self.logger.warning(f'{msg}. For more information and alternatives, refer to  {_EJS_WIKI_URL}')