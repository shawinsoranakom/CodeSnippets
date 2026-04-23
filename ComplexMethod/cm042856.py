def icourses_playlist_new(url, page=None):
    # 2 helpers using same interface in the js code
    def to_chap(course_id, chap_id, mod):
        ep = 'http://www.icourses.cn/jpk/viewCharacterDetail2.action?courseId={}&characId={}&mod={}'
        req = post_content(ep.format(course_id, chap_id, mod), post_data={})
        return req

    def to_sec(course_id, chap_id, mod):
        ep = 'http://www.icourses.cn/jpk/viewCharacterDetail2.action?courseId={}&characId={}&mod={}'
        req = post_content(ep.format(course_id, chap_id, mod), post_data={})
        return req

    def show_sec(course_id, chap_id):
        ep = 'http://www.icourses.cn/jpk/getSectionNode.action?courseId={}&characId={}&mod=2'
        req = post_content(ep.format(course_id, chap_id), post_data={})
        return req

    if page is None:
        page = get_content(url)
    chap_patt = r'<h3>.+?id="parent_row_(\d+)".+?onclick="(\w+)\((.+)\)"'
    to_chap_patt = r'this,(\d+),(\d+),(\d)'
    show_sec_patt = r'this,(\d+),(\d+)'
    res_patt = r'res_showResDetail\(\'(\d+)\',\'.+?\',\'\d+\',\'mp4\',\'(\d+)\'\)'
    l = re.findall(chap_patt, page)
    for i in l:
        if i[1] == 'ajaxtocharac':
            hit = re.search(to_chap_patt, i[2])
            page = to_chap(hit.group(1), hit.group(2), hit.group(3))
            hit_list = re.findall(res_patt, page)
            if hit_list:
                return get_playlist(hit_list[0][0], hit_list[0][1])
            for hit in hit_list:
                print(hit)
        elif i[1] == 'showSectionNode2':
            hit = re.search(show_sec_patt, i[2])
            page = show_sec(hit.group(1), hit.group(2))
            # print(page)
            patt = r'ajaxtosection\(this,(\d+),(\d+),(\d+)\)'
            hit_list = re.findall(patt, page)
            # print(hit_list)
            for hit in hit_list:
                page = to_sec(hit[0], hit[1], hit[2])
                vlist = re.findall(res_patt, page)
                if vlist:
                    return get_playlist(vlist[0][0], vlist[0][1])
    raise Exception("No video found in this playlist")