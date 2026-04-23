def tokenize_with_weights(self, text:str, return_word_ids=False, tokenizer_options={}, **kwargs):
        '''
        Takes a prompt and converts it to a list of (token, weight, word id) elements.
        Tokens can both be integer tokens and pre computed CLIP tensors.
        Word id values are unique per word and embedding, where the id 0 is reserved for non word tokens.
        Returned list has the dimensions NxM where M is the input size of CLIP
        '''
        min_length = tokenizer_options.get("{}_min_length".format(self.embedding_key), self.min_length)
        min_padding = tokenizer_options.get("{}_min_padding".format(self.embedding_key), self.min_padding)

        min_length = kwargs.get("min_length", min_length)

        text = escape_important(text)
        if kwargs.get("disable_weights", self.disable_weights):
            parsed_weights = [(text, 1.0)]
        else:
            parsed_weights = token_weights(text, 1.0)

        # tokenize words
        tokens = []
        for weighted_segment, weight in parsed_weights:
            to_tokenize = unescape_important(weighted_segment)
            split = re.split(' {0}|\n{0}'.format(self.embedding_identifier), to_tokenize)
            to_tokenize = [split[0]]
            for i in range(1, len(split)):
                to_tokenize.append("{}{}".format(self.embedding_identifier, split[i]))

            to_tokenize = [x for x in to_tokenize if x != ""]
            for word in to_tokenize:
                # if we find an embedding, deal with the embedding
                if word.startswith(self.embedding_identifier) and self.embedding_directory is not None:
                    embedding_name = word[len(self.embedding_identifier):].strip('\n')
                    embed, leftover = self._try_get_embedding(embedding_name)
                    if embed is None:
                        logging.warning(f"warning, embedding:{embedding_name} does not exist, ignoring")
                    else:
                        if len(embed.shape) == 1:
                            tokens.append([(embed, weight)])
                        else:
                            tokens.append([(embed[x], weight) for x in range(embed.shape[0])])
                    #if we accidentally have leftover text, continue parsing using leftover, else move on to next word
                    if leftover != "":
                        word = leftover
                    else:
                        continue
                end = 999999999999
                if self.tokenizer_adds_end_token:
                    end = -1
                #parse word
                tokens.append([(t, weight) for t in self.tokenizer(word)["input_ids"][self.tokens_start:end]])

        #reshape token array to CLIP input size
        batched_tokens = []
        batch = []
        if self.start_token is not None:
            batch.append((self.start_token, 1.0, 0))
        batched_tokens.append(batch)
        for i, t_group in enumerate(tokens):
            #determine if we're going to try and keep the tokens in a single batch
            is_large = len(t_group) >= self.max_word_length
            if self.end_token is not None:
                has_end_token = 1
            else:
                has_end_token = 0

            while len(t_group) > 0:
                if len(t_group) + len(batch) > self.max_length - has_end_token:
                    remaining_length = self.max_length - len(batch) - has_end_token
                    #break word in two and add end token
                    if is_large:
                        batch.extend([(t,w,i+1) for t,w in t_group[:remaining_length]])
                        if self.end_token is not None:
                            batch.append((self.end_token, 1.0, 0))
                        t_group = t_group[remaining_length:]
                    #add end token and pad
                    else:
                        if self.end_token is not None:
                            batch.append((self.end_token, 1.0, 0))
                        if self.pad_to_max_length:
                            self.pad_tokens(batch, remaining_length)
                    #start new batch
                    batch = []
                    if self.start_token is not None:
                        batch.append((self.start_token, 1.0, 0))
                    batched_tokens.append(batch)
                else:
                    batch.extend([(t,w,i+1) for t,w in t_group])
                    t_group = []

        #fill last batch
        if self.end_token is not None:
            batch.append((self.end_token, 1.0, 0))
        if min_padding is not None:
            self.pad_tokens(batch, min_padding)
        if self.pad_to_max_length and len(batch) < self.max_length:
            self.pad_tokens(batch, self.max_length - len(batch))
        if min_length is not None and len(batch) < min_length:
            self.pad_tokens(batch, min_length - len(batch))

        if not return_word_ids:
            batched_tokens = [[(t, w) for t, w,_ in x] for x in batched_tokens]

        return batched_tokens