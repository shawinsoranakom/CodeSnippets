def _real_extract(self, url):
        username, slug = self._match_valid_url(url).groups()
        username, slug = compat_urllib_parse_unquote(username), compat_urllib_parse_unquote(slug)
        track_id = '%s_%s' % (username, slug)

        cloudcast = self._call_api('cloudcast', '''audioLength
    comments(first: 100) {
      edges {
        node {
          comment
          created
          user {
            displayName
            username
          }
        }
      }
      totalCount
    }
    description
    favorites {
      totalCount
    }
    featuringArtistList
    isExclusive
    name
    owner {
      displayName
      url
      username
    }
    picture(width: 1024, height: 1024) {
        url
    }
    plays
    publishDate
    reposts {
      totalCount
    }
    streamInfo {
      dashUrl
      hlsUrl
      url
    }
    tags {
      tag {
        name
      }
    }''', track_id, username, slug)

        title = cloudcast['name']

        stream_info = cloudcast['streamInfo']
        formats = []

        for url_key in ('url', 'hlsUrl', 'dashUrl'):
            format_url = stream_info.get(url_key)
            if not format_url:
                continue
            decrypted = self._decrypt_xor_cipher(
                self._DECRYPTION_KEY, compat_b64decode(format_url))
            if url_key == 'hlsUrl':
                formats.extend(self._extract_m3u8_formats(
                    decrypted, track_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif url_key == 'dashUrl':
                formats.extend(self._extract_mpd_formats(
                    decrypted, track_id, mpd_id='dash', fatal=False))
            else:
                formats.append({
                    'format_id': 'http',
                    'url': decrypted,
                    'downloader_options': {
                        # Mixcloud starts throttling at >~5M
                        'http_chunk_size': 5242880,
                    },
                })

        if not formats and cloudcast.get('isExclusive'):
            self.raise_login_required()

        self._sort_formats(formats)

        comments = []
        for edge in (try_get(cloudcast, lambda x: x['comments']['edges']) or []):
            node = edge.get('node') or {}
            text = strip_or_none(node.get('comment'))
            if not text:
                continue
            user = node.get('user') or {}
            comments.append({
                'author': user.get('displayName'),
                'author_id': user.get('username'),
                'text': text,
                'timestamp': parse_iso8601(node.get('created')),
            })

        tags = []
        for t in cloudcast.get('tags'):
            tag = try_get(t, lambda x: x['tag']['name'], compat_str)
            if not tag:
                tags.append(tag)

        get_count = lambda x: int_or_none(try_get(cloudcast, lambda y: y[x]['totalCount']))

        owner = cloudcast.get('owner') or {}

        return {
            'id': track_id,
            'title': title,
            'formats': formats,
            'description': cloudcast.get('description'),
            'thumbnail': try_get(cloudcast, lambda x: x['picture']['url'], compat_str),
            'uploader': owner.get('displayName'),
            'timestamp': parse_iso8601(cloudcast.get('publishDate')),
            'uploader_id': owner.get('username'),
            'uploader_url': owner.get('url'),
            'duration': int_or_none(cloudcast.get('audioLength')),
            'view_count': int_or_none(cloudcast.get('plays')),
            'like_count': get_count('favorites'),
            'repost_count': get_count('reposts'),
            'comment_count': get_count('comments'),
            'comments': comments,
            'tags': tags,
            'artist': ', '.join(cloudcast.get('featuringArtistList') or []) or None,
        }