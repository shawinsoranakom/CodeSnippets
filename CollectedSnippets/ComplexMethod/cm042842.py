def ximalaya_download_by_id(id, title = None, output_dir = '.', info_only = False, stream_id = None):
    BASE_URL = 'http://www.ximalaya.com/tracks/'
    json_url = BASE_URL + id + '.json'
    json_data = json.loads(get_content(json_url, headers=fake_headers))
    if 'res' in json_data:
        if json_data['res'] == False:
            raise ValueError('Server reported id %s is invalid' % id)
    if 'is_paid' in json_data and json_data['is_paid']:
        if 'is_free' in json_data and not json_data['is_free']:
            raise ValueError('%s is paid item' % id)
    if (not title) and 'title' in json_data:
        title = json_data['title']
#no size data in the json. should it be calculated?
    size = 0
    url = json_data['play_path_64']
    if stream_id:
        if stream_id == '1':
            url = json_data['play_path_32']
        elif stream_id == '0':
            url = json_data['play_path']
    logging.debug('ximalaya_download_by_id: %s' % url)
    ext = 'm4a' 
    urls = [url]
    print('Site:        %s' % site_info)
    print('title:       %s' % title)
    if info_only:
        if stream_id:
            print_stream_info(stream_id)
        else:
            for item in range(0, len(stream_types)):
                print_stream_info(item)
    if not info_only:
        print('Type:        MPEG-4 audio m4a')
        print('Size:        N/A')
        download_urls(urls, title, ext, size, output_dir = output_dir, merge = False)