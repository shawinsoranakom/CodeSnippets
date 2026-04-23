def _get_comments(self, video_id):
        pages_total = None
        for page_n in itertools.count():
            raw_comments = self._download_json(
                f'{_API_BASE_URL}comment?postId={video_id[5:]}&page={page_n}&size=50',
                video_id, note=f'Downloading viewer comments page {page_n + 1}{format_field(pages_total, None, " of %s")}',
                fatal=False) or {}

            for comment in raw_comments.get('content') or []:
                yield {
                    'text': str_or_none(comment.get('comment')),
                    'author': str_or_none(comment.get('name')),
                    'id': comment.get('commentId'),
                    'author_id': comment.get('userId'),
                    'parent': 'root',
                    'like_count': int_or_none(comment.get('numLikes')),
                    'dislike_count': int_or_none(comment.get('numDislikes')),
                    'timestamp': unified_timestamp(comment.get('postedAt')),
                }

            pages_total = int_or_none(raw_comments.get('totalPages')) or None
            is_last = raw_comments.get('last')
            if not raw_comments.get('content') or is_last or (page_n > pages_total if pages_total else is_last is not False):
                return