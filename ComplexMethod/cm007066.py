def split_text_base(self):
        separator = self._fix_separator(self.separator)
        separator = unescape_string(separator)

        if isinstance(self.data_inputs, DataFrame):
            if not len(self.data_inputs):
                msg = "DataFrame is empty"
                raise TypeError(msg)

            self.data_inputs.text_key = self.text_key
            try:
                documents = self.data_inputs.to_lc_documents()
            except Exception as e:
                msg = f"Error converting DataFrame to documents: {e}"
                raise TypeError(msg) from e
        elif isinstance(self.data_inputs, Message):
            self.data_inputs = [self.data_inputs.to_data()]
            return self.split_text_base()
        else:
            if not self.data_inputs:
                msg = "No data inputs provided"
                raise TypeError(msg)

            documents = []
            if isinstance(self.data_inputs, Data):
                self.data_inputs.text_key = self.text_key
                documents = [self.data_inputs.to_lc_document()]
            else:
                try:
                    documents = [input_.to_lc_document() for input_ in self.data_inputs if isinstance(input_, Data)]
                    if not documents:
                        msg = f"No valid Data inputs found in {type(self.data_inputs)}"
                        raise TypeError(msg)
                except AttributeError as e:
                    msg = f"Invalid input type in collection: {e}"
                    raise TypeError(msg) from e
        try:
            # Convert string 'False'/'True' to boolean
            keep_sep = self.keep_separator
            if isinstance(keep_sep, str):
                if keep_sep.lower() == "false":
                    keep_sep = False
                elif keep_sep.lower() == "true":
                    keep_sep = True
                # 'start' and 'end' are kept as strings

            splitter = CharacterTextSplitter(
                chunk_overlap=self.chunk_overlap,
                chunk_size=self.chunk_size,
                separator=separator,
                keep_separator=keep_sep,
            )
            return splitter.split_documents(documents)
        except Exception as e:
            msg = f"Error splitting text: {e}"
            raise TypeError(msg) from e