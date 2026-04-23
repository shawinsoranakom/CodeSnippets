def _real_extract(self, url):
        clip_id = self._match_id(url)

        clip = self._download_json(
            'https://proxy-base.master.mango.express/graphql',
            clip_id, data=json.dumps({
                "query": """{
  viewer {
    clip(id: "%s") {
      title
      description
      duration
      createdAt
      ageRestriction
      videoFiles {
        edges {
          node {
            publicLocation
            fileSize
            videoProfile {
              width
              height
              bitrate
              encoding
            }
          }
        }
      }
      captionFiles {
        edges {
          node {
            publicLocation
          }
        }
      }
      teaserImages {
        edges {
          node {
            imageFiles {
              edges {
                node {
                  publicLocation
                  width
                  height
                }
              }
            }
          }
        }
      }
    }
  }
}""" % clip_id}).encode(), headers={
                'Content-Type': 'application/json',
            })['data']['viewer']['clip']
        title = clip['title']

        formats = []
        for edge in clip.get('videoFiles', {}).get('edges', []):
            node = edge.get('node', {})
            n_url = node.get('publicLocation')
            if not n_url:
                continue
            ext = determine_ext(n_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    n_url, clip_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                video_profile = node.get('videoProfile', {})
                tbr = int_or_none(video_profile.get('bitrate'))
                format_id = 'http'
                if tbr:
                    format_id += '-%d' % tbr
                formats.append({
                    'format_id': format_id,
                    'url': n_url,
                    'width': int_or_none(video_profile.get('width')),
                    'height': int_or_none(video_profile.get('height')),
                    'tbr': tbr,
                    'filesize': int_or_none(node.get('fileSize')),
                })
        self._sort_formats(formats)

        subtitles = {}
        for edge in clip.get('captionFiles', {}).get('edges', []):
            node = edge.get('node', {})
            n_url = node.get('publicLocation')
            if not n_url:
                continue
            subtitles.setdefault('de', []).append({
                'url': n_url,
            })

        thumbnails = []
        for edge in clip.get('teaserImages', {}).get('edges', []):
            for image_edge in edge.get('node', {}).get('imageFiles', {}).get('edges', []):
                node = image_edge.get('node', {})
                n_url = node.get('publicLocation')
                if not n_url:
                    continue
                thumbnails.append({
                    'url': n_url,
                    'width': int_or_none(node.get('width')),
                    'height': int_or_none(node.get('height')),
                })

        return {
            'id': clip_id,
            'title': title,
            'description': clip.get('description'),
            'duration': int_or_none(clip.get('duration')),
            'timestamp': parse_iso8601(clip.get('createdAt')),
            'age_limit': int_or_none(clip.get('ageRestriction')),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
        }