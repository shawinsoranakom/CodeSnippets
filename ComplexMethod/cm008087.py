def _real_extract(self, url):
        username, slug = self._match_valid_url(url).groups()
        username, slug = urllib.parse.unquote(username), urllib.parse.unquote(slug)
        track_id = f'{username}_{slug}'

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
    }
    restrictedReason
    id''', track_id, username, slug)

        if not cloudcast:
            raise ExtractorError('Track not found', expected=True)

        reason = cloudcast.get('restrictedReason')
        if reason == 'tracklist':
            raise ExtractorError('Track unavailable in your country due to licensing restrictions', expected=True)
        elif reason == 'repeat_play':
            raise ExtractorError('You have reached your play limit for this track', expected=True)
        elif reason:
            raise ExtractorError('Track is restricted', expected=True)

        stream_info = cloudcast['streamInfo']
        formats = []

        for url_key in ('url', 'hlsUrl', 'dashUrl'):
            format_url = stream_info.get(url_key)
            if not format_url:
                continue
            decrypted = self._decrypt_xor_cipher(
                self._DECRYPTION_KEY, base64.b64decode(format_url))
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
                    'vcodec': 'none',
                    'downloader_options': {
                        # Mixcloud starts throttling at >~5M
                        'http_chunk_size': 5242880,
                    },
                })

        if not formats and cloudcast.get('isExclusive'):
            self.raise_login_required(metadata_available=True)

        comments = []
        for node in traverse_obj(cloudcast, ('comments', 'edges', ..., 'node', {dict})):
            text = strip_or_none(node.get('comment'))
            if not text:
                continue
            comments.append({
                'text': text,
                **traverse_obj(node, {
                    'author': ('user', 'displayName', {str}),
                    'author_id': ('user', 'username', {str}),
                    'timestamp': ('created', {parse_iso8601}),
                }),
            })

        return {
            'id': track_id,
            'formats': formats,
            'comments': comments,
            **traverse_obj(cloudcast, {
                'title': ('name', {str}),
                'description': ('description', {str}),
                'thumbnail': ('picture', 'url', {url_or_none}),
                'timestamp': ('publishDate', {parse_iso8601}),
                'duration': ('audioLength', {int_or_none}),
                'uploader': ('owner', 'displayName', {str}),
                'uploader_id': ('owner', 'username', {str}),
                'uploader_url': ('owner', 'url', {url_or_none}),
                'view_count': ('plays', {int_or_none}),
                'like_count': ('favorites', 'totalCount', {int_or_none}),
                'repost_count': ('reposts', 'totalCount', {int_or_none}),
                'comment_count': ('comments', 'totalCount', {int_or_none}),
                'tags': ('tags', ..., 'tag', 'name', {str}, filter, all, filter),
                'artists': ('featuringArtistList', ..., {str}, filter, all, filter),
            }),
        }