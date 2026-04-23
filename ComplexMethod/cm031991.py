def step_2_core_key_translate():

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # step2
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    def load_string(strings, string_input):
        string_ = string_input.strip().strip(',').strip().strip('.').strip()
        if string_.startswith('[Local Message]'):
            string_ = string_.replace('[Local Message]', '')
            string_ = string_.strip().strip(',').strip().strip('.').strip()
        splitted_string = [string_]
        # --------------------------------------
        splitted_string = advanced_split(splitted_string, spliter="，", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="。", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="）", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="（", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="(", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter=")", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="<", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter=">", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="[", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="]", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="【", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="】", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="？", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="：", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter=":", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter=",", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="#", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="\n", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter=";", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="`", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="   ", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="- ", include_spliter=False)
        splitted_string = advanced_split(splitted_string, spliter="---", include_spliter=False)

        # --------------------------------------
        for j, s in enumerate(splitted_string): # .com
            if '.com' in s: continue
            if '\'' in s: continue
            if '\"' in s: continue
            strings.append([s,0])


    def get_strings(node):
        strings = []
        # recursively traverse the AST
        for child in ast.iter_child_nodes(node):
            node = child
            if isinstance(child, ast.Str):
                if contains_chinese(child.s):
                    load_string(strings=strings, string_input=child.s)
            elif isinstance(child, ast.AST):
                strings.extend(get_strings(child))
        return strings

    string_literals = []
    directory_path = f'./multi-language/{LANG}/'
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                syntax = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # comments
                    comments_arr = []
                    for code_sp in content.splitlines():
                        comments = re.findall(r'#.*$', code_sp)
                        for comment in comments:
                            load_string(strings=comments_arr, string_input=comment)
                    string_literals.extend(comments_arr)

                    # strings
                    import ast
                    tree = ast.parse(content)
                    res = get_strings(tree, )
                    string_literals.extend(res)

    [print(s) for s in string_literals]
    chinese_literal_names = []
    chinese_literal_names_norepeat = []
    for string, offset in string_literals:
        chinese_literal_names.append(string)
    chinese_literal_names_norepeat = []
    for d in chinese_literal_names:
        if d not in chinese_literal_names_norepeat: chinese_literal_names_norepeat.append(d)
    need_translate = []
    cached_translation = read_map_from_json(language=LANG)
    cached_translation_keys = list(cached_translation.keys())
    for d in chinese_literal_names_norepeat:
        if d not in cached_translation_keys:
            need_translate.append(d)

    if CACHE_ONLY:
        up = {}
    else:
        up = trans_json(need_translate, language=LANG, special=False)
    map_to_json(up, language=LANG)
    cached_translation = read_map_from_json(language=LANG)
    LANG_STD = 'std'
    cached_translation.update(read_map_from_json(language=LANG_STD))
    cached_translation = dict(sorted(cached_translation.items(), key=lambda x: -len(x[0])))

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # literal key replace
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    directory_path = f'./multi-language/{LANG}/'
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                syntax = []
                # read again
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for k, v in cached_translation.items():
                    if v is None: continue
                    if '"' in v:
                        v = v.replace('"', "`")
                    if '\'' in v:
                        v = v.replace('\'', "`")
                    content = content.replace(k, v)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                if file.strip('.py') in cached_translation:
                    file_new = cached_translation[file.strip('.py')] + '.py'
                    file_path_new = os.path.join(root, file_new)
                    with open(file_path_new, 'w', encoding='utf-8') as f:
                        f.write(content)
                    os.remove(file_path)