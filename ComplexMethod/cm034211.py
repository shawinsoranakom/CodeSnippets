def _add_seealso(text: list[str], seealsos: list[dict[str, t.Any]], limit: int, opt_indent: str) -> None:
        for item in seealsos:
            if 'module' in item:
                text.append(DocCLI.warp_fill(DocCLI.tty_ify('Module %s' % item['module']),
                            limit - 6, initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
                description = item.get('description')
                if description is None and item['module'].startswith('ansible.builtin.'):
                    description = 'The official documentation on the %s module.' % item['module']
                if description is not None:
                    text.append(DocCLI.warp_fill(DocCLI.tty_ify(description),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                if item['module'].startswith('ansible.builtin.'):
                    relative_url = 'collections/%s_module.html' % item['module'].replace('.', '/', 2)
                    text.append(DocCLI.warp_fill(DocCLI.tty_ify(get_versioned_doclink(relative_url)),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent))
            elif 'plugin' in item and 'plugin_type' in item:
                plugin_suffix = ' plugin' if item['plugin_type'] not in ('module', 'role') else ''
                text.append(DocCLI.warp_fill(DocCLI.tty_ify('%s%s %s' % (item['plugin_type'].title(), plugin_suffix, item['plugin'])),
                            limit - 6, initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
                description = item.get('description')
                if description is None and item['plugin'].startswith('ansible.builtin.'):
                    description = 'The official documentation on the %s %s%s.' % (item['plugin'], item['plugin_type'], plugin_suffix)
                if description is not None:
                    text.append(DocCLI.warp_fill(DocCLI.tty_ify(description),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                if item['plugin'].startswith('ansible.builtin.'):
                    relative_url = 'collections/%s_%s.html' % (item['plugin'].replace('.', '/', 2), item['plugin_type'])
                    text.append(DocCLI.warp_fill(DocCLI.tty_ify(get_versioned_doclink(relative_url)),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent))
            elif 'name' in item and 'link' in item and 'description' in item:
                text.append(DocCLI.warp_fill(DocCLI.tty_ify(item['name']),
                            limit - 6, initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
                text.append(DocCLI.warp_fill(DocCLI.tty_ify(item['description']),
                            limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                text.append(DocCLI.warp_fill(DocCLI.tty_ify(item['link']),
                            limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
            elif 'ref' in item and 'description' in item:
                text.append(DocCLI.warp_fill(DocCLI.tty_ify('Ansible documentation [%s]' % item['ref']),
                            limit - 6, initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
                text.append(DocCLI.warp_fill(DocCLI.tty_ify(item['description']),
                            limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                text.append(DocCLI.warp_fill(DocCLI.tty_ify(get_versioned_doclink('/#stq=%s&stp=1' % item['ref'])),
                            limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))