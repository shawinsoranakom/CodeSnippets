def _set_language(self, type):
        lang = type[0]
        assert type, "please use -l or --language to choose language type"
        assert lang in support_list.keys() or lang in multi_lang, (
            "the sub_keys(-l or --language) can only be one of support list: \n{},\nbut get: {}, "
            "please check your running command".format(multi_lang, type)
        )
        if lang in latin_lang:
            lang = "latin"
        elif lang in arabic_lang:
            lang = "arabic"
        elif lang in cyrillic_lang:
            lang = "cyrillic"
        elif lang in devanagari_lang:
            lang = "devanagari"
        global_config["Global"]["character_dict_path"] = (
            "ppocr/utils/dict/{}_dict.txt".format(lang)
        )
        global_config["Global"]["save_model_dir"] = "./output/rec_{}_lite".format(lang)
        global_config["Train"]["dataset"]["label_file_list"] = [
            "train_data/{}_train.txt".format(lang)
        ]
        global_config["Eval"]["dataset"]["label_file_list"] = [
            "train_data/{}_val.txt".format(lang)
        ]
        global_config["Global"]["character_type"] = lang
        assert os.path.isfile(
            os.path.join(project_path, global_config["Global"]["character_dict_path"])
        ), "Loss default dictionary file {}_dict.txt.You can download it from \
https://github.com/PaddlePaddle/PaddleOCR/tree/dygraph/ppocr/utils/dict/".format(
            lang
        )
        return lang