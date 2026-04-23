def __init__(self, hparams, val=False):
        exp_dir = hparams.exp_dir
        self.path2 = "%s/2-name2text.txt" % exp_dir
        self.path4 = "%s/4-cnhubert" % exp_dir
        self.path5 = "%s/5-wav32k" % exp_dir
        assert os.path.exists(self.path2)
        assert os.path.exists(self.path4)
        assert os.path.exists(self.path5)
        names4 = set([name[:-3] for name in list(os.listdir(self.path4))])  # 去除.pt后缀
        names5 = set(os.listdir(self.path5))
        self.phoneme_data = {}
        with open(self.path2, "r", encoding="utf8") as f:
            lines = f.read().strip("\n").split("\n")

        for line in lines:
            tmp = line.split("\t")
            if len(tmp) != 4:
                continue
            self.phoneme_data[tmp[0]] = [tmp[1]]

        self.audiopaths_sid_text = list(set(self.phoneme_data) & names4 & names5)
        tmp = self.audiopaths_sid_text
        leng = len(tmp)
        min_num = 100
        if leng < min_num:
            self.audiopaths_sid_text = []
            for _ in range(max(2, int(min_num / leng))):
                self.audiopaths_sid_text += tmp
        self.max_wav_value = hparams.max_wav_value
        self.sampling_rate = hparams.sampling_rate
        self.filter_length = hparams.filter_length
        self.hop_length = hparams.hop_length
        self.win_length = hparams.win_length
        self.sampling_rate = hparams.sampling_rate
        self.val = val

        random.seed(1234)
        random.shuffle(self.audiopaths_sid_text)

        print("phoneme_data_len:", len(self.phoneme_data.keys()))
        print("wav_data_len:", len(self.audiopaths_sid_text))

        audiopaths_sid_text_new = []
        lengths = []
        skipped_phone = 0
        skipped_dur = 0
        for audiopath in tqdm(self.audiopaths_sid_text):
            try:
                phoneme = self.phoneme_data[audiopath][0]
                phoneme = phoneme.split(" ")
                phoneme_ids = cleaned_text_to_sequence(phoneme, version)
            except Exception:
                print(f"{audiopath} not in self.phoneme_data !")
                skipped_phone += 1
                continue

            size = os.path.getsize("%s/%s" % (self.path5, audiopath))
            duration = size / self.sampling_rate / 2

            if duration == 0:
                print(f"Zero duration for {audiopath}, skipping...")
                skipped_dur += 1
                continue

            if 54 > duration > 0.6 or self.val:
                audiopaths_sid_text_new.append([audiopath, phoneme_ids])
                lengths.append(size // (2 * self.hop_length))
            else:
                skipped_dur += 1
                continue

        print("skipped_phone: ", skipped_phone, ", skipped_dur: ", skipped_dur)
        print("total left: ", len(audiopaths_sid_text_new))
        assert len(audiopaths_sid_text_new) > 1  # 至少能凑够batch size，这里todo
        self.audiopaths_sid_text = audiopaths_sid_text_new
        self.lengths = lengths
        self.spec_min = -12
        self.spec_max = 2

        self.filter_length_mel = self.win_length_mel = 1280
        self.hop_length_mel = 320
        self.n_mel_channels = 100
        self.sampling_rate_mel = 32000
        self.mel_fmin = 0
        self.mel_fmax = None