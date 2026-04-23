def post_create(self, forum, post_parent=None, **post):
        if is_html_empty(post.get('content', '')):
            return request.render('http_routing.http_error', {
                'status_code': _('Bad Request'),
                'status_message': post_parent and _('Reply should not be empty.') or _('Question should not be empty.')
            })

        post_tag_ids = forum._tag_to_write_vals(post.get('post_tags', ''))
        slug = request.env['ir.http']._slug
        if forum.has_pending_post:
            return request.redirect("/forum/%s/ask" % slug(forum))

        new_question = request.env['forum.post'].create({
            'forum_id': forum.id,
            'name': post.get('post_name') or (post_parent and 'Re: %s' % (post_parent.name or '')) or '',
            'content': post.get('content', False),
            'parent_id': post_parent and post_parent.id or False,
            'tag_ids': post_tag_ids
        })
        if post_parent:
            post_parent._update_last_activity()
        slug = request.env['ir.http']._slug
        return request.redirect(f'/forum/{slug(forum)}/{slug(post_parent) if post_parent else new_question.id}')