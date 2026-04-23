def icourses_playlist_download(url, output_dir='.', **kwargs):
    page_type_patt = r'showSectionNode\(this,(\d+),(\d+)\)'
    resid_courseid_patt = r'changeforvideo\(\'(\d+)\',\'(\d+)\',\'(\d+)\'\)'
    ep = 'http://www.icourses.cn/jpk/viewCharacterDetail.action?sectionId={}&courseId={}'
    change_for_video_ip = 'http://www.icourses.cn/jpk/changeforVideo.action?resId={}&courseId={}'
    video_list = []

    if 'viewVCourse' in url:
        playlist = public_course_playlist(url)
        for video in playlist:
            icourses_download(video[0], output_dir=output_dir, **kwargs)
        return
    elif 'coursestatic' in url:
        course_page = get_content(url)
        page_navi_vars = re.search(page_type_patt, course_page)

        if page_navi_vars is None:  # type 2 shared course
            video_list = icourses_playlist_new(url, course_page)
        else:  # type 1 shared course
            sec_page = get_content(ep.format(page_navi_vars.group(2), page_navi_vars.group(1)))
            video_list = re.findall(resid_courseid_patt, sec_page)
    elif 'viewCharacterDetail.action' in url or 'changeforVideo.action' in url:
        page = get_content(url)
        video_list = re.findall(resid_courseid_patt, page)

    if not video_list:
        raise Exception('Unknown url pattern')

    for video in video_list:
        video_url = change_for_video_ip.format(video[0], video[1])
        sleep(random.Random().randint(0, 5))  # Prevent from blockage
        icourses_download(video_url, output_dir=output_dir, **kwargs)