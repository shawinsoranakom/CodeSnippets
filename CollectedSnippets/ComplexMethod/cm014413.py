def add_embedding(
        self,
        mat,
        metadata=None,
        label_img=None,
        global_step=None,
        tag="default",
        metadata_header=None,
    ) -> None:
        """Add embedding projector data to summary.

        Args:
            mat (torch.Tensor or numpy.ndarray): A matrix which each row is the feature vector of the data point
            metadata (list): A list of labels, each element will be converted to string
            label_img (torch.Tensor): Images correspond to each data point
            global_step (int): Global step value to record
            tag (str): Name for the embedding
            metadata_header (list): A list of headers for multi-column metadata. If given, each metadata must be
                a list with values corresponding to headers.
        Shape:
            mat: :math:`(N, D)`, where N is number of data and D is feature dimension

            label_img: :math:`(N, C, H, W)`

        Examples::

            import keyword
            import torch
            meta = []
            while len(meta)<100:
                meta = meta+keyword.kwlist # get some strings
            meta = meta[:100]

            for i, v in enumerate(meta):
                meta[i] = v+str(i)

            label_img = torch.rand(100, 3, 10, 32)
            for i in range(100):
                label_img[i]*=i/100.0

            writer.add_embedding(torch.randn(100, 5), metadata=meta, label_img=label_img)
            writer.add_embedding(torch.randn(100, 5), label_img=label_img)
            writer.add_embedding(torch.randn(100, 5), metadata=meta)

        .. note::
            Categorical (i.e. non-numeric) metadata cannot have more than 50 unique values if they are to be used for
            coloring in the embedding projector.

        """
        torch._C._log_api_usage_once("tensorboard.logging.add_embedding")
        mat = make_np(mat)
        if global_step is None:
            global_step = 0
            # clear pbtxt?

        # Maybe we should encode the tag so slashes don't trip us up?
        # I don't think this will mess us up, but better safe than sorry.
        subdir = f"{str(global_step).zfill(5)}/{self._encode(tag)}"
        save_path = os.path.join(self._get_file_writer().get_logdir(), subdir)

        fs = tf.io.gfile
        if fs.exists(save_path):
            if fs.isdir(save_path):
                print(
                    "warning: Embedding dir exists, did you set global_step for add_embedding()?"
                )
            else:
                raise NotADirectoryError(
                    f"Path: `{save_path}` exists, but is a file. Cannot proceed."
                )
        else:
            fs.makedirs(save_path)

        if metadata is not None:
            if mat.shape[0] != len(
                metadata
            ):
                raise AssertionError("#labels should equal with #data points")
            make_tsv(metadata, save_path, metadata_header=metadata_header)

        if label_img is not None:
            if mat.shape[0] != label_img.shape[0]:
                raise AssertionError("#images should equal with #data points")
            make_sprite(label_img, save_path)

        if mat.ndim != 2:
            raise AssertionError("mat should be 2D, where mat.size(0) is the number of data points")
        make_mat(mat, save_path)

        # Filesystem doesn't necessarily have append semantics, so we store an
        # internal buffer to append to and re-write whole file after each
        # embedding is added
        if not hasattr(self, "_projector_config"):
            self._projector_config = ProjectorConfig()
        embedding_info = get_embedding_info(
            metadata, label_img, subdir, global_step, tag
        )
        self._projector_config.embeddings.extend([embedding_info])


        from google.protobuf import text_format

        config_pbtxt = text_format.MessageToString(self._projector_config)
        write_pbtxt(self._get_file_writer().get_logdir(), config_pbtxt)