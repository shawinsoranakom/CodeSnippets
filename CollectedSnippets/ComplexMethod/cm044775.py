def init_batch(self):
        semantic_data_len = len(self.semantic_data)
        phoneme_data_len = len(self.phoneme_data.keys())
        print("semantic_data_len:", semantic_data_len)
        print("phoneme_data_len:", phoneme_data_len)
        print(self.semantic_data)
        idx = 0
        num_not_in = 0
        num_deleted_bigger = 0
        num_deleted_ps = 0
        for i in range(semantic_data_len):
            # 先依次遍历
            # get str
            item_name = self.semantic_data.iloc[i, 0]
            # print(self.phoneme_data)
            try:
                phoneme, word2ph, text = self.phoneme_data[item_name]
            except Exception:
                traceback.print_exc()
                print(f"Warning: File \"{item_name}\" not in self.phoneme_data! Skipped. ")
                num_not_in += 1
                continue

            semantic_str = self.semantic_data.iloc[i, 1]
            # get token list
            semantic_ids = [int(idx) for idx in semantic_str.split(" ")]
            # (T), 是否需要变成 (1, T) -> 不需要，因为需要求 len
            # 过滤掉太长的样本
            if (
                len(semantic_ids) > self.max_sec * self.hz
            ):  #########1###根据token个数推测总时长过滤时长60s（config里）#40*25=1k
                num_deleted_bigger += 1
                continue
            # (T, ), 这个速度不会很慢，所以可以在一开始就处理，无需在 __getitem__ 里面单个处理####
            phoneme = phoneme.split(" ")

            try:
                phoneme_ids = cleaned_text_to_sequence(phoneme, version)
            except:
                traceback.print_exc()
                print(f"Warning: Failed to convert phonemes to sequence for file \"{item_name}\"! Skipped. ")
                num_not_in += 1
                continue
            # if len(phoneme_ids) >400:###########2：改为恒定限制为semantic/2.5就行
            if len(phoneme_ids) > self.max_sec * self.hz / 2.5:  ###########2：改为恒定限制为semantic/2.5就行
                num_deleted_ps += 1
                continue
            # if len(semantic_ids) > 1000:###########3
            #     num_deleted_bigger += 1
            #     continue

            ps_ratio = len(phoneme_ids) / (len(semantic_ids) / self.hz)

            if ps_ratio > self.max_ps_ratio or ps_ratio < self.min_ps_ratio:  ##########4#3~25#每秒多少个phone
                num_deleted_ps += 1
                # print(item_name)
                continue

            self.semantic_phoneme.append((semantic_ids, phoneme_ids))
            idx += 1
            self.item_names.append(item_name)

        min_num = 100  # 20直接不补#30补了也不存ckpt
        leng = len(self.semantic_phoneme)
        if leng < min_num:
            tmp1 = self.semantic_phoneme
            tmp2 = self.item_names
            self.semantic_phoneme = []
            self.item_names = []
            for _ in range(max(2, int(min_num / leng))):
                self.semantic_phoneme += tmp1
                self.item_names += tmp2
        if num_not_in > 0:
            print(f"there are {num_not_in} semantic datas not in phoneme datas")
        if num_deleted_bigger > 0:
            print(
                f"deleted {num_deleted_bigger} audios who's duration are bigger than {self.max_sec} seconds",
            )
        if num_deleted_ps > 0:
            # 4702 for LibriTTS, LirbriTTS 是标注数据, 是否需要筛？=> 需要，有值为 100 的极端值
            print(
                f"deleted {num_deleted_ps} audios who's phoneme/sec are bigger than {self.max_ps_ratio} or smaller than {self.min_ps_ratio}",
            )
        """
        there are 31 semantic datas not in phoneme datas
        deleted 34 audios who's duration are bigger than 54 seconds
        deleted 3190 audios who's phoneme/sec are bigger than 25 or smaller than 3
        dataset.__len__(): 366463

        """
        # 345410 for LibriTTS
        print("dataset.__len__():", self.__len__())