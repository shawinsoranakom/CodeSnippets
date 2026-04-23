def _yi_sandhi(self, word: str, finals: List[str]) -> List[str]:
        # "一" in number sequences, e.g. 一零零, 二一零
        if word.find("一") != -1 and all([item.isnumeric() for item in word if item != "一"]):
            return finals
        # "一" between reduplication words shold be yi5, e.g. 看一看
        elif len(word) == 3 and word[1] == "一" and word[0] == word[-1]:
            finals[1] = finals[1][:-1] + "5"
        # when "一" is ordinal word, it should be yi1
        elif word.startswith("第一"):
            finals[1] = finals[1][:-1] + "1"
        else:
            for i, char in enumerate(word):
                if char == "一" and i + 1 < len(word):
                    # "一" before tone4 should be yi2, e.g. 一段
                    if finals[i + 1][-1] == "4":
                        finals[i] = finals[i][:-1] + "2"
                    # "一" before non-tone4 should be yi4, e.g. 一天
                    else:
                        # "一" 后面如果是标点，还读一声
                        if word[i + 1] not in self.punc:
                            finals[i] = finals[i][:-1] + "4"
        return finals