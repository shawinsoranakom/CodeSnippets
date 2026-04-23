def _neural_sandhi(self, word: str, pos: str, finals: List[str]) -> List[str]:
        # reduplication words for n. and v. e.g. 奶奶, 试试, 旺旺
        for j, item in enumerate(word):
            if (
                j - 1 >= 0
                and item == word[j - 1]
                and pos[0] in {"n", "v", "a"}
                and word not in self.must_not_neural_tone_words
            ):
                finals[j] = finals[j][:-1] + "5"
        ge_idx = word.find("个")
        if len(word) >= 1 and word[-1] in "吧呢哈啊呐噻嘛吖嗨呐哦哒额滴哩哟喽啰耶喔诶":
            finals[-1] = finals[-1][:-1] + "5"
        elif len(word) >= 1 and word[-1] in "的地得":
            finals[-1] = finals[-1][:-1] + "5"
        # e.g. 走了, 看着, 去过
        elif len(word) == 1 and word in "了着过" and pos in {"ul", "uz", "ug"}:
            finals[-1] = finals[-1][:-1] + "5"
        elif len(word) > 1 and word[-1] in "们子" and pos in {"r", "n"} and word not in self.must_not_neural_tone_words:
            finals[-1] = finals[-1][:-1] + "5"
        # e.g. 桌上, 地下, 家里
        elif len(word) > 1 and word[-1] in "上下里" and pos in {"s", "l", "f"}:
            finals[-1] = finals[-1][:-1] + "5"
        # e.g. 上来, 下去
        elif len(word) > 1 and word[-1] in "来去" and word[-2] in "上下进出回过起开":
            finals[-1] = finals[-1][:-1] + "5"
        # 个做量词
        elif (
            ge_idx >= 1 and (word[ge_idx - 1].isnumeric() or word[ge_idx - 1] in "几有两半多各整每做是")
        ) or word == "个":
            finals[ge_idx] = finals[ge_idx][:-1] + "5"
        else:
            if word in self.must_neural_tone_words or word[-2:] in self.must_neural_tone_words:
                finals[-1] = finals[-1][:-1] + "5"

        word_list = self._split_word(word)
        finals_list = [finals[: len(word_list[0])], finals[len(word_list[0]) :]]
        for i, word in enumerate(word_list):
            # conventional neural in Chinese
            if word in self.must_neural_tone_words or word[-2:] in self.must_neural_tone_words:
                finals_list[i][-1] = finals_list[i][-1][:-1] + "5"
        finals = sum(finals_list, [])
        return finals