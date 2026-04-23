def load_assets(self, dir_path):
        if self.input_vocabulary is not None:
            # Vocab saved in config.
            # TODO: consider unifying both paths.
            return
        vocabulary_filepath = tf.io.gfile.join(dir_path, "vocabulary.txt")
        with open(vocabulary_filepath, "r") as f:
            lines = f.read().splitlines()
            while lines and lines[-1] == "":
                lines.pop()
            if tf.as_dtype(self.vocabulary_dtype) == tf.string:
                values = [str(line) for line in lines]
            else:
                values = [int(line) for line in lines]
            if self.output_mode == "tf_idf":
                idf_weights = self.idf_weights_const.numpy()
                self.set_vocabulary(values, idf_weights=idf_weights)
            else:
                self.set_vocabulary(values)