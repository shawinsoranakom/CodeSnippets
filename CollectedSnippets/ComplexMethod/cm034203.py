def display_plugin_list(self, results):

        # format for user
        displace = max(len(x) for x in results.keys())
        linelimit = display.columns - displace - 5
        text = []
        deprecated = []

        # format display per option
        if context.CLIARGS['list_files']:
            # list plugin file names
            for plugin in sorted(results.keys()):
                filename = to_native(results[plugin])

                # handle deprecated for builtin/legacy
                pbreak = plugin.split('.')
                if pbreak[-1].startswith('_') and pbreak[0] == 'ansible' and pbreak[1] in ('builtin', 'legacy'):
                    pbreak[-1] = pbreak[-1][1:]
                    plugin = '.'.join(pbreak)
                    deprecated.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(filename), filename))
                else:
                    text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(filename), filename))
        else:
            # list plugin names and short desc
            for plugin in sorted(results.keys()):
                desc = DocCLI.tty_ify(results[plugin])

                if len(desc) > linelimit:
                    desc = desc[:linelimit] + '...'

                pbreak = plugin.split('.')
                # TODO: add mark for deprecated collection plugins
                if pbreak[-1].startswith('_') and plugin.startswith(('ansible.builtin.', 'ansible.legacy.')):
                    # Handle deprecated ansible.builtin plugins
                    pbreak[-1] = pbreak[-1][1:]
                    plugin = '.'.join(pbreak)
                    deprecated.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(desc), desc))
                else:
                    text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(desc), desc))

        if len(deprecated) > 0:
            text.append("\nDEPRECATED:")
            text.extend(deprecated)

        # display results
        DocCLI.pager("\n".join(text))