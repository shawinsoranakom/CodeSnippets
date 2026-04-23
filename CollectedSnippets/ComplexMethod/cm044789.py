def qryword(self, o_word):
        word = o_word.lower()

        # 查字典, 单字母除外
        if len(word) > 1 and word in self.cmu:  # lookup CMU dict
            return self.cmu[word][0]

        # 单词仅首字母大写时查找姓名字典
        if o_word.istitle() and word in self.namedict:
            return self.namedict[word][0]

        # oov 长度小于等于 3 直接读字母
        if len(word) <= 3:
            phones = []
            for w in word:
                # 单读 A 发音修正, 此处不存在大写的情况
                if w == "a":
                    phones.extend(["EY1"])
                elif not w.isalpha():
                    phones.extend([w])
                else:
                    phones.extend(self.cmu[w][0])
            return phones

        # 尝试分离所有格
        if re.match(r"^([a-z]+)('s)$", word):
            phones = self.qryword(word[:-2])[:]
            # P T K F TH HH 无声辅音结尾 's 发 ['S']
            if phones[-1] in ["P", "T", "K", "F", "TH", "HH"]:
                phones.extend(["S"])
            # S Z SH ZH CH JH 擦声结尾 's 发 ['IH1', 'Z'] 或 ['AH0', 'Z']
            elif phones[-1] in ["S", "Z", "SH", "ZH", "CH", "JH"]:
                phones.extend(["AH0", "Z"])
            # B D G DH V M N NG L R W Y 有声辅音结尾 's 发 ['Z']
            # AH0 AH1 AH2 EY0 EY1 EY2 AE0 AE1 AE2 EH0 EH1 EH2 OW0 OW1 OW2 UH0 UH1 UH2 IY0 IY1 IY2 AA0 AA1 AA2 AO0 AO1 AO2
            # ER ER0 ER1 ER2 UW0 UW1 UW2 AY0 AY1 AY2 AW0 AW1 AW2 OY0 OY1 OY2 IH IH0 IH1 IH2 元音结尾 's 发 ['Z']
            else:
                phones.extend(["Z"])
            return phones

        # 尝试进行分词，应对复合词
        comps = wordsegment.segment(word.lower())

        # 无法分词的送回去预测
        if len(comps) == 1:
            return self.predict(word)

        # 可以分词的递归处理
        return [phone for comp in comps for phone in self.qryword(comp)]