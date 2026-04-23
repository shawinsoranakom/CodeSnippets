def traverse_json_ld(json_ld, at_top_level=True):
            for e in variadic(json_ld):
                if not isinstance(e, dict):
                    continue
                if at_top_level and '@context' not in e:
                    continue
                if at_top_level and set(e.keys()) == {'@context', '@graph'}:
                    traverse_json_ld(e['@graph'], at_top_level=False)
                    continue
                if expected_type is not None and not is_type(e, expected_type):
                    continue
                rating = traverse_obj(e, ('aggregateRating', 'ratingValue'), expected_type=float_or_none)
                if rating is not None:
                    info['average_rating'] = rating
                if is_type(e, 'TVEpisode', 'Episode', 'PodcastEpisode'):
                    episode_name = unescapeHTML(e.get('name'))
                    info.update({
                        'episode': episode_name,
                        'episode_number': int_or_none(e.get('episodeNumber')),
                        'description': unescapeHTML(e.get('description')),
                    })
                    if not info.get('title') and episode_name:
                        info['title'] = episode_name
                    part_of_season = e.get('partOfSeason')
                    if is_type(part_of_season, 'TVSeason', 'Season', 'CreativeWorkSeason'):
                        info.update({
                            'season': unescapeHTML(part_of_season.get('name')),
                            'season_number': int_or_none(part_of_season.get('seasonNumber')),
                        })
                    part_of_series = e.get('partOfSeries') or e.get('partOfTVSeries')
                    if is_type(part_of_series, 'TVSeries', 'Series', 'CreativeWorkSeries'):
                        info['series'] = unescapeHTML(part_of_series.get('name'))
                elif is_type(e, 'Movie'):
                    info.update({
                        'title': unescapeHTML(e.get('name')),
                        'description': unescapeHTML(e.get('description')),
                        'duration': parse_duration(e.get('duration')),
                        'timestamp': unified_timestamp(e.get('dateCreated')),
                    })
                elif is_type(e, 'Article', 'NewsArticle'):
                    info.update({
                        'timestamp': parse_iso8601(e.get('datePublished')),
                        'title': unescapeHTML(e.get('headline')),
                        'description': unescapeHTML(e.get('articleBody') or e.get('description')),
                    })
                    if is_type(traverse_obj(e, ('video', 0)), 'VideoObject'):
                        extract_video_object(e['video'][0])
                    elif is_type(traverse_obj(e, ('subjectOf', 0)), 'VideoObject'):
                        extract_video_object(e['subjectOf'][0])
                elif is_type(e, 'VideoObject', 'AudioObject'):
                    extract_video_object(e)
                    if expected_type is None:
                        continue
                    else:
                        break
                video = e.get('video')
                if is_type(video, 'VideoObject'):
                    extract_video_object(video)
                if expected_type is None:
                    continue
                else:
                    break