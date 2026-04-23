def process_options(options):
        for option in options.values():
            if not isinstance(option, MutableMapping):
                continue
            if 'version_added' in option:
                callback(option, 'version_added', 'version_added_collection')
            if not is_module:
                if isinstance(option.get('env'), list):
                    process_option_specifiers(option['env'])
                if isinstance(option.get('ini'), list):
                    process_option_specifiers(option['ini'])
                if isinstance(option.get('vars'), list):
                    process_option_specifiers(option['vars'])
                if isinstance(option.get('deprecated'), MutableMapping):
                    process_deprecation(option['deprecated'])
            if isinstance(option.get('suboptions'), MutableMapping):
                process_options(option['suboptions'])