def getTexts(text,default_lang = ""):
        lang_splitter = LangSplitter(lang_map=LangSegmenter.DEFAULT_LANG_MAP)
        lang_splitter.merge_across_digit = False
        substr = lang_splitter.split_by_lang(text=text)

        lang_list: list[dict] = []

        have_num = False

        for _, item in enumerate(substr):
            dict_item = {'lang':item.lang,'text':item.text}

            if dict_item['lang'] == 'digit':
                if default_lang != "":
                    dict_item['lang'] = default_lang
                else:
                    have_num = True
                lang_list = merge_lang(lang_list,dict_item)
                continue

            # 处理短英文被识别为其他语言的问题
            if full_en(dict_item['text']):  
                dict_item['lang'] = 'en'
                lang_list = merge_lang(lang_list,dict_item)
                continue

            if default_lang != "":
                dict_item['lang'] = default_lang
                lang_list = merge_lang(lang_list,dict_item)
                continue
            else:
                # 处理非日语夹日文的问题(不包含CJK)
                ja_list: list[dict] = []
                if dict_item['lang'] != 'ja':
                    ja_list = split_jako('ja',dict_item)

                if not ja_list:
                    ja_list.append(dict_item)

                # 处理非韩语夹韩语的问题(不包含CJK)
                ko_list: list[dict] = []
                temp_list: list[dict] = []
                for _, ko_item in enumerate(ja_list):
                    if ko_item["lang"] != 'ko':
                        ko_list = split_jako('ko',ko_item)

                    if ko_list:
                        temp_list.extend(ko_list)
                    else:
                        temp_list.append(ko_item)

                # 未存在非日韩文夹日韩文
                if len(temp_list) == 1:
                    # 未知语言检查是否为CJK
                    if dict_item['lang'] == 'x':
                        cjk_text = full_cjk(dict_item['text'])
                        if cjk_text:
                            dict_item = {'lang':'zh','text':cjk_text}
                            lang_list = merge_lang(lang_list,dict_item)
                        else:
                            lang_list = merge_lang(lang_list,dict_item)
                        continue
                    else:
                        lang_list = merge_lang(lang_list,dict_item)
                        continue

                # 存在非日韩文夹日韩文
                for _, temp_item in enumerate(temp_list):
                    # 未知语言检查是否为CJK
                    if temp_item['lang'] == 'x':
                        cjk_text = full_cjk(temp_item['text'])
                        if cjk_text:
                            lang_list = merge_lang(lang_list,{'lang':'zh','text':cjk_text})
                        else:
                            lang_list = merge_lang(lang_list,temp_item)
                    else:
                        lang_list = merge_lang(lang_list,temp_item)

        # 有数字
        if have_num:
            temp_list = lang_list
            lang_list = []
            for i, temp_item in enumerate(temp_list):
                if temp_item['lang'] == 'digit':
                    if default_lang:
                        temp_item['lang'] = default_lang
                    elif lang_list and i == len(temp_list) - 1:
                        temp_item['lang'] = lang_list[-1]['lang']
                    elif not lang_list and i < len(temp_list) - 1:
                        temp_item['lang'] = temp_list[1]['lang']
                    elif lang_list and i < len(temp_list) - 1:
                        if lang_list[-1]['lang'] == temp_list[i + 1]['lang']:
                            temp_item['lang'] = lang_list[-1]['lang']
                        elif lang_list[-1]['text'][-1] in [",",".","!","?","，","。","！","？"]:
                            temp_item['lang'] = temp_list[i + 1]['lang']
                        elif temp_list[i + 1]['text'][0] in [",",".","!","?","，","。","！","？"]:
                            temp_item['lang'] = lang_list[-1]['lang']
                        elif temp_item['text'][-1] in ["。","."]:
                            temp_item['lang'] = lang_list[-1]['lang']
                        elif len(lang_list[-1]['text']) >= len(temp_list[i + 1]['text']):
                            temp_item['lang'] = lang_list[-1]['lang']
                        else:
                            temp_item['lang'] = temp_list[i + 1]['lang']
                    else:
                        temp_item['lang'] = 'zh'

                lang_list = merge_lang(lang_list,temp_item)


        # 筛X
        temp_list = lang_list
        lang_list = []
        for _, temp_item in enumerate(temp_list):
            if temp_item['lang'] == 'x':
                if lang_list:
                    temp_item['lang'] = lang_list[-1]['lang']
                elif len(temp_list) > 1:
                    temp_item['lang'] = temp_list[1]['lang']
                else:
                    temp_item['lang'] = 'zh'

            lang_list = merge_lang(lang_list,temp_item)

        return lang_list