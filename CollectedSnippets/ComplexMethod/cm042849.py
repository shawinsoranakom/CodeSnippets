def fetch_magic(cls, url):
        def search_dict(a_dict, target):
            for key, val in a_dict.items():
                if val == target:
                    return key

        magic_list = []

        page = get_content(url)
        src = re.findall(r'src="(.+?)"', page)
        js = [path for path in src if path.endswith('.js')]

        host = 'http://' + urllib.parse.urlparse(url).netloc
        js_path = [urllib.parse.urljoin(host, rel_path) for rel_path in js]

        for p in js_path:
            if 'mtool' in p or 'mcore' in p:
                js_text = get_content(p)
                hit = re.search(r'\(\'(.+?)\',(\d+),(\d+),\'(.+?)\'\.split\(\'\|\'\),\d+,\{\}\)', js_text)

                code = hit.group(1)
                base = hit.group(2)
                size = hit.group(3)
                names = hit.group(4).split('|')

                mapping = KBaseMapping(base=int(base))
                sym_to_name = {}
                for no in range(int(size), 0, -1):
                    no_in_base = mapping.mapping(no)
                    val = names[no] if no < len(names) and names[no] else no_in_base
                    sym_to_name[no_in_base] = val

                moz_ec_name = search_dict(sym_to_name, 'mozEcName')
                push = search_dict(sym_to_name, 'push')
                patt = r'{}\.{}\("(.+?)"\)'.format(moz_ec_name, push)
                ec_list = re.findall(patt, code)
                [magic_list.append(sym_to_name[ec]) for ec in ec_list]
        return magic_list