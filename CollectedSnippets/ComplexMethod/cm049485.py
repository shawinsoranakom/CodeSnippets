def _tag_to_write_vals(self, tags=''):
        Tag = self.env['forum.tag']
        post_tags = []
        existing_keep = []
        user = self.env.user
        for tag_id_or_new_name in (tag.strip() for tag in tags.split(',') if tag and tag.strip()):
            if tag_id_or_new_name.startswith('_'):  # it's a new tag
                tag_name = tag_id_or_new_name[1:]
                # check that not already created meanwhile or maybe excluded by the limit on the search
                tag_ids = Tag.search([('name', '=', tag_name), ('forum_id', '=', self.id)], limit=1)
                if tag_ids:
                    existing_keep.append(tag_ids.id)
                else:
                    # check if user have Karma needed to create need tag
                    if user.exists() and user.karma >= self.karma_tag_create and tag_name:
                        post_tags.append((0, 0, {'name': tag_name, 'forum_id': self.id}))
            else:
                existing_keep.append(int(tag_id_or_new_name))
        post_tags.insert(0, [6, 0, existing_keep])
        return post_tags