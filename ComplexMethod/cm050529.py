def _extract_tags_and_users(self):
        tags = []
        users = []
        tags_and_users_group = self._get_group_pattern()['tags_and_users']
        for word in re.findall(tags_and_users_group % '', self.display_name):
            (tags if word.startswith('#') else users).append(word[1:])
        users_to_keep = []
        user_ids = []
        for user in users:
            matched_users = self.env['res.users'].name_search(user)
            if len(matched_users) == 1:
                user_ids.append(Command.link(matched_users[0][0]))
            else:
                users_to_keep.append(r'%s\b' % user)
        self.user_ids = user_ids
        if tags:
            domain = Domain.OR(Domain('name', '=ilike', tag) for tag in tags)
            existing_tags = self.env['project.tags'].search(domain)
            existing_tags_names = {tag.name.lower() for tag in existing_tags}
            new_tags_names = {tag for tag in tags if tag.lower() not in existing_tags_names}
            self.tag_ids = [Command.set(existing_tags.ids)] + [Command.create({'name': name}) for name in new_tags_names]
        pattern = tags_and_users_group % ('(?!%s)' % ('|').join(users_to_keep) if users_to_keep else '')
        self.display_name, _ = re.subn(pattern, '', self.display_name)