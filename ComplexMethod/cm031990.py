def step_1_core_key_translate():
    LANG_STD = 'std'
    def extract_chinese_characters(file_path):
        syntax = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            import ast
            root = ast.parse(content)
            for node in ast.walk(root):
                if isinstance(node, ast.Name):
                    if contains_chinese(node.id): syntax.append(node.id)
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if contains_chinese(n.name): syntax.append(n.name)
                elif isinstance(node, ast.ImportFrom):
                    for n in node.names:
                        if contains_chinese(n.name): syntax.append(n.name)
                        # if node.module is None: print(node.module)
                        for k in node.module.split('.'):
                            if contains_chinese(k): syntax.append(k)
            return syntax

    def extract_chinese_characters_from_directory(directory_path):
        chinese_characters = []
        for root, dirs, files in os.walk(directory_path):
            if any([b in root for b in blacklist]):
                continue
            print(files)
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    chinese_characters.extend(extract_chinese_characters(file_path))
        return chinese_characters

    directory_path = './'
    chinese_core_names = extract_chinese_characters_from_directory(directory_path)
    chinese_core_keys = [name for name in chinese_core_names]
    chinese_core_keys_norepeat = []
    for d in chinese_core_keys:
        if d not in chinese_core_keys_norepeat: chinese_core_keys_norepeat.append(d)
    need_translate = []
    cached_translation = read_map_from_json(language=LANG_STD)
    cached_translation_keys = list(cached_translation.keys())
    for d in chinese_core_keys_norepeat:
        if d not in cached_translation_keys:
            need_translate.append(d)

    if CACHE_ONLY:
        need_translate_mapping = {}
    else:
        need_translate_mapping = trans(need_translate, language=LANG_STD, special=True)
    map_to_json(need_translate_mapping, language=LANG_STD)
    cached_translation = read_map_from_json(language=LANG_STD)
    cached_translation = dict(sorted(cached_translation.items(), key=lambda x: -len(x[0])))

    chinese_core_keys_norepeat_mapping = {}
    for k in chinese_core_keys_norepeat:
        chinese_core_keys_norepeat_mapping.update({k:cached_translation[k]})
    chinese_core_keys_norepeat_mapping = dict(sorted(chinese_core_keys_norepeat_mapping.items(), key=lambda x: -len(x[0])))

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # copy
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def copy_source_code():

        from toolbox import get_conf
        import shutil
        import os
        try: shutil.rmtree(f'./multi-language/{LANG}/')
        except: pass
        os.makedirs(f'./multi-language', exist_ok=True)
        backup_dir = f'./multi-language/{LANG}/'
        shutil.copytree('./', backup_dir, ignore=lambda x, y: blacklist)
    copy_source_code()

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # primary key replace
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

                for k, v in chinese_core_keys_norepeat_mapping.items():
                    content = content.replace(k, v)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)