def tucao_single_download(type_link, title, output_dir=".", merge=True, info_only=False):
    if "file" in type_link:
        url=type_link[type_link.find("file=")+5:]
        vtype, ext, size=url_info(url)
        print_info(site_info, title, vtype, size)
        if not info_only:
            download_urls([url], title, ext, size, output_dir)
    #fix for 189 video source, see raw list types 7
    elif "189" in type_link:
        vid = match1(type_link, r"vid=(\d+)")
        assert vid, "vid not exsits"
        url = "http://api.tucao.tv/api/down/{}".format(vid)
        vtype, ext, size=url_info(url)
        print_info(site_info, title, vtype, size)
        if not info_only:
            download_urls([url], title, ext, size, output_dir)
    else:
        u="http://www.tucao.tv/api/playurl.php?{}&key=tucao{:07x}.cc&r={}".format(type_link,random.getrandbits(28),int(time.time()*1000))
        xml=minidom.parseString(get_content(u))
        urls=[]
        size=0
        for i in xml.getElementsByTagName("url"):
            urls.append(i.firstChild.nodeValue)
            vtype, ext, _size=url_info(i.firstChild.nodeValue)
            size+=_size
        print_info(site_info, title, vtype, size)
        if not info_only:
            download_urls(urls, title, ext, size, output_dir)