def icourses_download(url, output_dir='.', **kwargs):
    if 'showResDetail.action' in url:
        hit = re.search(r'id=(\d+)&courseId=(\d+)', url)
        url = 'http://www.icourses.cn/jpk/changeforVideo.action?resId={}&courseId={}'.format(hit.group(1), hit.group(2))
    if re.match(r'http://www.icourses.cn/coursestatic/course_(\d+).html', url):
        raise Exception('You can download it with -l flag')
    icourses_parser = ICousesExactor(url=url)
    icourses_parser.basic_extract()
    title = icourses_parser.title
    size = None
    for i in range(5):
        try:
            # use this url only for size
            size_url = icourses_parser.generate_url(0)
            _, type_, size = url_info(size_url, headers=fake_headers)
        except error.HTTPError:
            logging.warning('Failed to fetch the video file! Retrying...')
            sleep(random.Random().randint(2, 5))  # Prevent from blockage
        else:
            print_info(site_info, title, type_, size)
            break

    if size is None:
        raise Exception("Failed")

    if not kwargs['info_only']:
        real_url = icourses_parser.update_url(0)
        headers = fake_headers.copy()
        headers['Referer'] = url
        download_urls_icourses(real_url, title, 'flv',total_size=size, output_dir=output_dir, max_size=15728640, dyn_callback=icourses_parser.update_url)
    return