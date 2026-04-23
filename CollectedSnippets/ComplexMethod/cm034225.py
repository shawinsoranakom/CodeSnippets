def execute_search(self):
        """ searches for roles on the Ansible Galaxy server"""
        page_size = 1000
        search = None

        if context.CLIARGS['args']:
            search = '+'.join(context.CLIARGS['args'])

        if not search and not context.CLIARGS['platforms'] and not context.CLIARGS['galaxy_tags'] and not context.CLIARGS['author']:
            raise AnsibleError("Invalid query. At least one search term, platform, galaxy tag or author must be provided.")

        response = self.api.search_roles(search, platforms=context.CLIARGS['platforms'],
                                         tags=context.CLIARGS['galaxy_tags'], author=context.CLIARGS['author'], page_size=page_size)

        if response['count'] == 0:
            display.warning("No roles match your search.")
            return 0

        data = [u'']

        if response['count'] > page_size:
            data.append(u"Found %d roles matching your search. Showing first %s." % (response['count'], page_size))
        else:
            data.append(u"Found %d roles matching your search:" % response['count'])

        max_len = []
        for role in response['results']:
            max_len.append(len(role['username'] + '.' + role['name']))
        name_len = max(max_len)
        format_str = u" %%-%ds %%s" % name_len
        data.append(u'')
        data.append(format_str % (u"Name", u"Description"))
        data.append(format_str % (u"----", u"-----------"))
        for role in response['results']:
            data.append(format_str % (u'%s.%s' % (role['username'], role['name']), role['description']))

        data = u'\n'.join(data)
        self.pager(data)

        return 0