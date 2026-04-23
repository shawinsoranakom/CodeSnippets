def _get_comments(self, post_id):
        cursor = None
        count = 0
        params = {
            'page[count]': 50,
            'include': 'parent.commenter.campaign,parent.post.user,parent.post.campaign.creator,parent.replies.parent,parent.replies.commenter.campaign,parent.replies.post.user,parent.replies.post.campaign.creator,commenter.campaign,post.user,post.campaign.creator,replies.parent,replies.commenter.campaign,replies.post.user,replies.post.campaign.creator,on_behalf_of_campaign',
            'fields[comment]': 'body,created,is_by_creator',
            'fields[user]': 'image_url,full_name,url',
            'filter[flair]': 'image_tiny_url,name',
            'sort': '-created',
            'json-api-version': 1.0,
            'json-api-use-default-includes': 'false',
        }

        for page in itertools.count(1):

            params.update({'page[cursor]': cursor} if cursor else {})
            response = self._call_api(
                f'posts/{post_id}/comments', post_id, query=params, note=f'Downloading comments page {page}')

            cursor = None
            for comment in traverse_obj(response, (('data', 'included'), lambda _, v: v['type'] == 'comment' and v['id'])):
                count += 1
                author_id = traverse_obj(comment, ('relationships', 'commenter', 'data', 'id'))

                yield {
                    **traverse_obj(comment, {
                        'id': ('id', {str_or_none}),
                        'text': ('attributes', 'body', {str}),
                        'timestamp': ('attributes', 'created', {parse_iso8601}),
                        'parent': ('relationships', 'parent', 'data', ('id', {value('root')}), {str}, any),
                        'author_is_uploader': ('attributes', 'is_by_creator', {bool}),
                    }),
                    **traverse_obj(response, (
                        'included', lambda _, v: v['id'] == author_id and v['type'] == 'user', 'attributes', {
                            'author': ('full_name', {str}),
                            'author_thumbnail': ('image_url', {url_or_none}),
                        }), get_all=False),
                    'author_id': author_id,
                }

            if count < traverse_obj(response, ('meta', 'count')):
                cursor = traverse_obj(response, ('data', -1, 'id'))

            if cursor is None:
                break