def _json_ld(self, json_ld, video_id, fatal=True, expected_type=None):
        if isinstance(json_ld, compat_str):
            json_ld = self._parse_json(json_ld, video_id, fatal=fatal)
        if not json_ld:
            return {}
        info = {}
        if not isinstance(json_ld, (list, tuple, dict)):
            return info
        if isinstance(json_ld, dict):
            json_ld = [json_ld]

        INTERACTION_TYPE_MAP = {
            'CommentAction': 'comment',
            'AgreeAction': 'like',
            'DisagreeAction': 'dislike',
            'LikeAction': 'like',
            'DislikeAction': 'dislike',
            'ListenAction': 'view',
            'WatchAction': 'view',
            'ViewAction': 'view',
        }

        def extract_interaction_type(e):
            interaction_type = e.get('interactionType')
            if isinstance(interaction_type, dict):
                interaction_type = interaction_type.get('@type')
            return str_or_none(interaction_type)

        def extract_interaction_statistic(e):
            interaction_statistic = e.get('interactionStatistic')
            if isinstance(interaction_statistic, dict):
                interaction_statistic = [interaction_statistic]
            if not isinstance(interaction_statistic, list):
                return
            for is_e in interaction_statistic:
                if not isinstance(is_e, dict):
                    continue
                if is_e.get('@type') != 'InteractionCounter':
                    continue
                interaction_type = extract_interaction_type(is_e)
                if not interaction_type:
                    continue
                # For interaction count some sites provide string instead of
                # an integer (as per spec) with non digit characters (e.g. ",")
                # so extracting count with more relaxed str_to_int
                interaction_count = str_to_int(is_e.get('userInteractionCount'))
                if interaction_count is None:
                    continue
                count_kind = INTERACTION_TYPE_MAP.get(interaction_type.split('/')[-1])
                if not count_kind:
                    continue
                count_key = '%s_count' % count_kind
                if info.get(count_key) is not None:
                    continue
                info[count_key] = interaction_count

        def extract_video_object(e):
            assert e['@type'] == 'VideoObject'
            author = e.get('author')
            info.update({
                'url': url_or_none(e.get('contentUrl')),
                'title': unescapeHTML(e.get('name')),
                'description': unescapeHTML(e.get('description')),
                'thumbnail': url_or_none(e.get('thumbnailUrl') or e.get('thumbnailURL')),
                'duration': parse_duration(e.get('duration')),
                'timestamp': unified_timestamp(e.get('uploadDate')),
                # author can be an instance of 'Organization' or 'Person' types.
                # both types can have 'name' property(inherited from 'Thing' type). [1]
                # however some websites are using 'Text' type instead.
                # 1. https://schema.org/VideoObject
                'uploader': author.get('name') if isinstance(author, dict) else author if isinstance(author, compat_str) else None,
                'filesize': float_or_none(e.get('contentSize')),
                'tbr': int_or_none(e.get('bitrate')),
                'width': int_or_none(e.get('width')),
                'height': int_or_none(e.get('height')),
                'view_count': int_or_none(e.get('interactionCount')),
            })
            extract_interaction_statistic(e)

        for e in json_ld:
            if '@context' in e:
                item_type = e.get('@type')
                if expected_type is not None and expected_type != item_type:
                    continue
                if item_type in ('TVEpisode', 'Episode'):
                    episode_name = unescapeHTML(e.get('name'))
                    info.update({
                        'episode': episode_name,
                        'episode_number': int_or_none(e.get('episodeNumber')),
                        'description': unescapeHTML(e.get('description')),
                    })
                    if not info.get('title') and episode_name:
                        info['title'] = episode_name
                    part_of_season = e.get('partOfSeason')
                    if isinstance(part_of_season, dict) and part_of_season.get('@type') in ('TVSeason', 'Season', 'CreativeWorkSeason'):
                        info.update({
                            'season': unescapeHTML(part_of_season.get('name')),
                            'season_number': int_or_none(part_of_season.get('seasonNumber')),
                        })
                    part_of_series = e.get('partOfSeries') or e.get('partOfTVSeries')
                    if isinstance(part_of_series, dict) and part_of_series.get('@type') in ('TVSeries', 'Series', 'CreativeWorkSeries'):
                        info['series'] = unescapeHTML(part_of_series.get('name'))
                elif item_type == 'Movie':
                    info.update({
                        'title': unescapeHTML(e.get('name')),
                        'description': unescapeHTML(e.get('description')),
                        'duration': parse_duration(e.get('duration')),
                        'timestamp': unified_timestamp(e.get('dateCreated')),
                    })
                elif item_type in ('Article', 'NewsArticle'):
                    info.update({
                        'timestamp': parse_iso8601(e.get('datePublished')),
                        'title': unescapeHTML(e.get('headline')),
                        'description': unescapeHTML(e.get('articleBody')),
                    })
                elif item_type == 'VideoObject':
                    extract_video_object(e)
                    if expected_type is None:
                        continue
                    else:
                        break
                video = e.get('video')
                if isinstance(video, dict) and video.get('@type') == 'VideoObject':
                    extract_video_object(video)
                if expected_type is None:
                    continue
                else:
                    break
        return dict((k, v) for k, v in info.items() if v is not None)