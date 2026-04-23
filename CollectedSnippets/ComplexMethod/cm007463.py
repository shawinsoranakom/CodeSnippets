def _real_extract(self, url):
        vid = self._match_id(url)
        resp = self._download_json(
            'https://gql.trovo.live/', vid, data=json.dumps([{
                'query': '''{
  batchGetVodDetailInfo(params: {vids: ["%s"]}) {
    VodDetailInfos
  }
}''' % vid,
            }, {
                'query': '''{
  getCommentList(params: {appInfo: {postID: "%s"}, pageSize: 1000000000, preview: {}}) {
    commentList {
      author {
        nickName
        uid
      }
      commentID
      content
      createdAt
      parentID
    }
  }
}''' % vid,
            }]).encode(), headers={
                'Content-Type': 'application/json',
            })
        vod_detail_info = resp[0]['data']['batchGetVodDetailInfo']['VodDetailInfos'][vid]
        vod_info = vod_detail_info['vodInfo']
        title = vod_info['title']

        language = vod_info.get('languageName')
        formats = []
        for play_info in (vod_info.get('playInfos') or []):
            play_url = play_info.get('playUrl')
            if not play_url:
                continue
            format_id = play_info.get('desc')
            formats.append({
                'ext': 'mp4',
                'filesize': int_or_none(play_info.get('fileSize')),
                'format_id': format_id,
                'height': int_or_none(format_id[:-1]) if format_id else None,
                'language': language,
                'protocol': 'm3u8_native',
                'tbr': int_or_none(play_info.get('bitrate')),
                'url': play_url,
                'http_headers': {'Origin': 'https://trovo.live'},
            })
        self._sort_formats(formats)

        category = vod_info.get('categoryName')
        get_count = lambda x: int_or_none(vod_info.get(x + 'Num'))

        comment_list = try_get(resp, lambda x: x[1]['data']['getCommentList']['commentList'], list) or []
        comments = []
        for comment in comment_list:
            content = comment.get('content')
            if not content:
                continue
            author = comment.get('author') or {}
            parent = comment.get('parentID')
            comments.append({
                'author': author.get('nickName'),
                'author_id': str_or_none(author.get('uid')),
                'id': str_or_none(comment.get('commentID')),
                'text': content,
                'timestamp': int_or_none(comment.get('createdAt')),
                'parent': 'root' if parent == 0 else str_or_none(parent),
            })

        info = {
            'id': vid,
            'title': title,
            'formats': formats,
            'thumbnail': vod_info.get('coverUrl'),
            'timestamp': int_or_none(vod_info.get('publishTs')),
            'duration': int_or_none(vod_info.get('duration')),
            'view_count': get_count('watch'),
            'like_count': get_count('like'),
            'comment_count': get_count('comment'),
            'comments': comments,
            'categories': [category] if category else None,
        }
        info.update(self._extract_streamer_info(vod_detail_info))
        return info