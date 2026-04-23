def get_video_thumbnail(video_url):
    """ Computes the valid thumbnail image from given URL
        (or None in case of invalid URL).
    """
    source = get_video_source_data(video_url)
    if source is None:
        return None

    response = None
    platform, video_id = source[:2]
    with contextlib.suppress(requests.exceptions.RequestException):
        if platform == 'youtube':
            response = requests.get(f'https://img.youtube.com/vi/{video_id}/0.jpg', timeout=10)
        elif platform == 'vimeo':
            res = requests.get(f'http://vimeo.com/api/oembed.json?url={video_url}', timeout=10)
            if res.ok:
                data = res.json()
                response = requests.get(data['thumbnail_url'], timeout=10)
        elif platform == 'dailymotion':
            response = requests.get(f'https://www.dailymotion.com/thumbnail/video/{video_id}', timeout=10)
        elif platform == 'instagram':
            response = requests.get(f'https://www.instagram.com/p/{video_id}/media/?size=t', timeout=10)

    if response and response.ok:
        return image_process(response.content)
    return None