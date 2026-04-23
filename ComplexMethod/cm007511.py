def _parse_video_data(self, video_data):
        video_id = compat_str(video_data['id'])
        title = video_data['title']

        s3_extracted = False
        formats = []
        for source in video_data.get('videos', []):
            source_url = source.get('url')
            if not source_url:
                continue
            f = {
                'format_id': source.get('quality_level'),
                'fps': int_or_none(source.get('frame_rate')),
                'height': int_or_none(source.get('height')),
                'tbr': int_or_none(source.get('video_data_rate')),
                'width': int_or_none(source.get('width')),
                'url': source_url,
            }
            original_filename = source.get('original_filename')
            if original_filename:
                if not (f.get('height') and f.get('width')):
                    mobj = re.search(r'_(\d+)x(\d+)', original_filename)
                    if mobj:
                        f.update({
                            'height': int(mobj.group(2)),
                            'width': int(mobj.group(1)),
                        })
                if original_filename.startswith('s3://') and not s3_extracted:
                    formats.append({
                        'format_id': 'original',
                        'preference': 1,
                        'url': original_filename.replace('s3://', 'https://s3.amazonaws.com/'),
                    })
                    s3_extracted = True
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnail'),
            'upload_date': unified_strdate(video_data.get('start_date')),
            'duration': parse_duration(video_data.get('duration')),
            'view_count': str_to_int(video_data.get('playcount')),
            'formats': formats,
            'subtitles': self._parse_subtitles(video_data, 'vtt'),
        }