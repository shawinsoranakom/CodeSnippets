def get_video_source_data(video_url):
    """ Computes the valid source, document ID and regex match from given URL
        (or None in case of invalid URL).
    """
    if not video_url:
        return None

    if re.search(valid_url_regex, video_url):
        youtube_match = re.search(player_regexes['youtube'], video_url)
        if youtube_match:
            return ('youtube', youtube_match[2], youtube_match)
        vimeo_match = re.search(player_regexes['vimeo'], video_url)
        if vimeo_match:
            return ('vimeo', vimeo_match.group('id'), vimeo_match)
        dailymotion_match = re.search(player_regexes['dailymotion'], video_url)
        if dailymotion_match:
            return ('dailymotion', dailymotion_match.group("id"), dailymotion_match)
        instagram_match = re.search(player_regexes['instagram'], video_url)
        if instagram_match:
            return ('instagram', instagram_match[2], instagram_match)
        facebook_match = re.search(player_regexes["facebook"], video_url)
        if facebook_match:
            return ("facebook", facebook_match.group("id"), facebook_match)
    return None