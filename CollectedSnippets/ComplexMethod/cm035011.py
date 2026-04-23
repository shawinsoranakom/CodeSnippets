def __init__(self, config, mode, logger, seed=None):
        super(LaTeXOCRDataSet, self).__init__()
        self.logger = logger
        self.mode = mode.lower()

        global_config = config["Global"]
        dataset_config = config[mode]["dataset"]
        loader_config = config[mode]["loader"]

        pkl_path = dataset_config.pop("data")
        self.data_dir = dataset_config["data_dir"]
        self.min_dimensions = dataset_config.pop("min_dimensions")
        self.max_dimensions = dataset_config.pop("max_dimensions")
        self.batchsize = dataset_config.pop("batch_size_per_pair")
        self.keep_smaller_batches = dataset_config.pop("keep_smaller_batches")
        self.max_seq_len = global_config.pop("max_seq_len")
        self.rec_char_dict_path = global_config.pop("rec_char_dict_path")
        self.tokenizer = LatexOCRLabelEncode(self.rec_char_dict_path)

        file = open(pkl_path, "rb")
        data = pickle.load(file)
        temp = {}
        for k in data:
            if (
                self.min_dimensions[0] <= k[0] <= self.max_dimensions[0]
                and self.min_dimensions[1] <= k[1] <= self.max_dimensions[1]
            ):
                temp[k] = data[k]
        self.data = temp
        self.do_shuffle = loader_config["shuffle"]
        self.seed = seed

        if self.mode == "train" and self.do_shuffle:
            random.seed(self.seed)
        self.pairs = []
        for k in self.data:
            info = np.array(self.data[k], dtype=object)
            p = (
                paddle.randperm(len(info))
                if self.mode == "train" and self.do_shuffle
                else paddle.arange(len(info))
            )
            for i in range(0, len(info), self.batchsize):
                batch = info[p[i : i + self.batchsize]]
                if len(batch.shape) == 1:
                    batch = batch[None, :]
                if len(batch) < self.batchsize and not self.keep_smaller_batches:
                    continue
                self.pairs.append(batch)
        if self.do_shuffle:
            self.pairs = np.random.permutation(np.array(self.pairs, dtype=object))
        else:
            self.pairs = np.array(self.pairs, dtype=object)

        self.size = len(self.pairs)
        self.set_epoch_as_seed(self.seed, dataset_config)

        self.ops = create_operators(dataset_config["transforms"], global_config)
        self.ext_op_transform_idx = dataset_config.get("ext_op_transform_idx", 2)
        self.need_reset = True