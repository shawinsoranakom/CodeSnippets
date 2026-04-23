def __init__(self, save_dir="marian_converted"):
        assert Path(DEFAULT_REPO).exists(), "need git clone git@github.com:Helsinki-NLP/Tatoeba-Challenge.git"
        self.download_lang_info()
        self.model_results = json.load(open("Tatoeba-Challenge/models/released-model-results.json"))
        self.alpha3_to_alpha2 = {}
        for line in open(ISO_PATH):
            parts = line.split("\t")
            if len(parts[0]) == 3 and len(parts[3]) == 2:
                self.alpha3_to_alpha2[parts[0]] = parts[3]
        for line in LANG_CODE_PATH:
            parts = line.split(",")
            if len(parts[0]) == 3 and len(parts[1]) == 2:
                self.alpha3_to_alpha2[parts[0]] = parts[1]
        self.model_card_dir = Path(save_dir)
        self.tag2name = {}
        for key, value in GROUP_MEMBERS.items():
            self.tag2name[key] = value[0]