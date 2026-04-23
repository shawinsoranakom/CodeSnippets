def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        encoder_outputs: tuple[tuple[torch.FloatTensor]] | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.BoolTensor | None = None,
        past_key_values: Cache | None = None,
        doc_scores: torch.FloatTensor | None = None,
        context_input_ids: torch.LongTensor | None = None,
        context_attention_mask: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        output_retrieved: bool | None = None,
        n_docs: int | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | RetrievAugLMOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input sequence tokens in the vocabulary. [`RagConfig`], used to initialize the model, specifies
            which generator to use, it also specifies a compatible generator tokenizer. Use that tokenizer class to
            obtain the indices.

            [What are input IDs?](../glossary#input-ids)
        encoder_outputs (`tuple(tuple(torch.FloatTensor)`, *optional*)
            Tuple consists of (`generator_enc_last_hidden_state`, *optional*: `generator_enc_hidden_states`,
            *optional*: `generator_enc_attentions`). `generator_enc_last_hidden_state` of shape `(batch_size, n_docs *
            sequence_length, hidden_size)` is a sequence of hidden-states at the output of the last layer of the
            generator's encoder.

            Used by the ([`RagModel`]) model during decoding.
        decoder_input_ids (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Provide for generation tasks. `None` by default, construct as per instructions for the generator model
            you're using with your RAG instance.
        decoder_attention_mask (`torch.BoolTensor` of shape `(batch_size,  target_sequence_length)`, *optional*):
            Default behavior: generate a tensor that ignores pad tokens in `decoder_input_ids`. Causal mask will also
            be used by default.
        doc_scores (`torch.FloatTensor` of shape `(batch_size, config.n_docs)`):
            Score between each retrieved document embeddings (see `retrieved_doc_embeds`) and
            `question_encoder_last_hidden_state`. If the model has is not initialized with a `retriever` `doc_scores`
            has to be provided to the forward pass. `doc_scores` can be computed via
            `question_encoder_last_hidden_state` and `retrieved_doc_embeds`, see examples for more information.
        context_input_ids (`torch.LongTensor` of shape `(batch_size * config.n_docs, config.max_combined_length)`, *optional*, returned when *output_retrieved=True*):
            Input IDs post-processed from the retrieved documents and the question encoder `input_ids` by the
            retriever. If the model was not initialized with a `retriever` ``context_input_ids` has to be provided to
            the forward pass. `context_input_ids` are returned by [`~RagRetriever.__call__`].
        context_attention_mask (`torch.LongTensor` of shape `(batch_size * config.n_docs, config.max_combined_length)`,*optional*, returned when *output_retrieved=True*):
            Attention mask post-processed from the retrieved documents and the question encoder `input_ids` by the
            retriever. If the model has is not initialized with a `retriever` `context_attention_mask` has to be
            provided to the forward pass. `context_attention_mask` are returned by [`~RagRetriever.__call__`].
        output_retrieved (`bool`, *optional*):
            Whether or not to return the `retrieved_doc_embeds`, `retrieved_doc_ids`, `context_input_ids` and
            `context_attention_mask`. See returned tensors for more detail.
        n_docs (`int`, *optional*):
            The number of documents to retrieve.

        Example:

        ```python
        >>> from transformers import AutoTokenizer, RagRetriever, RagModel
        >>> import torch

        >>> tokenizer = AutoTokenizer.from_pretrained("facebook/rag-token-base")
        >>> retriever = RagRetriever.from_pretrained(
        ...     "facebook/rag-token-base", index_name="exact", use_dummy_dataset=True
        ... )
        >>> # initialize with RagRetriever to do everything in one forward call
        >>> model = RagModel.from_pretrained("facebook/rag-token-base", retriever=retriever)

        >>> inputs = tokenizer("How many people live in Paris?", return_tensors="pt")
        >>> outputs = model(input_ids=inputs["input_ids"])
        ```"""
        n_docs = n_docs if n_docs is not None else self.config.n_docs
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_retrieved = output_retrieved if output_retrieved is not None else self.config.output_retrieved

        # whether retriever has to be used
        has_to_retrieve = (
            self.retriever is not None
            and (context_input_ids is None or context_attention_mask is None or doc_scores is None)
            and encoder_outputs is None
        )
        # encoder_outputs are pre-computed during RAG-token generation
        if encoder_outputs is None:
            if has_to_retrieve:
                question_enc_outputs = self.question_encoder(
                    input_ids, attention_mask=attention_mask, return_dict=True
                )
                question_encoder_last_hidden_state = question_enc_outputs[0]  # hidden states of question encoder

                retriever_outputs = self.retriever(
                    input_ids,
                    question_encoder_last_hidden_state.detach().to(device="cpu", dtype=torch.float32).numpy(),
                    prefix=getattr(self.generator.config, "prefix", None),
                    n_docs=n_docs,
                    return_tensors="pt",
                )
                if self.context_encoder_training:
                    (
                        context_input_ids,
                        context_attention_mask,
                        retrieved_doc_embeds,
                        retrieved_doc_input_ids,
                        retrieved_doc_attention_mask,
                        retrieved_doc_ids,
                    ) = (
                        retriever_outputs["context_input_ids"],
                        retriever_outputs["context_attention_mask"],
                        retriever_outputs["retrieved_doc_embeds"],
                        retriever_outputs["tokenized_doc_ids"],
                        retriever_outputs["tokenized_doc_attention_mask"],
                        retriever_outputs["doc_ids"],
                    )

                    context_input_ids = context_input_ids.to(input_ids)
                    context_attention_mask = context_attention_mask.to(input_ids)

                    retrieved_doc_input_ids = retrieved_doc_input_ids.to(input_ids)
                    retrieved_doc_attention_mask = retrieved_doc_attention_mask.to(input_ids)
                    retrieved_doc_embeds = self.ctx_encoder(
                        retrieved_doc_input_ids, attention_mask=retrieved_doc_attention_mask, return_dict=True
                    ).pooler_output
                    retrieved_doc_embeds = retrieved_doc_embeds.view(
                        -1, n_docs, question_encoder_last_hidden_state.shape[1]
                    )  # reshaping

                    # compute doc_scores involving ctx_encoder
                    doc_scores = torch.bmm(
                        question_encoder_last_hidden_state.unsqueeze(1), retrieved_doc_embeds.transpose(1, 2)
                    ).squeeze(1)

                else:
                    context_input_ids, context_attention_mask, retrieved_doc_embeds, retrieved_doc_ids = (
                        retriever_outputs["context_input_ids"],
                        retriever_outputs["context_attention_mask"],
                        retriever_outputs["retrieved_doc_embeds"],
                        retriever_outputs["doc_ids"],
                    )

                    # set to correct device
                    retrieved_doc_embeds = retrieved_doc_embeds.to(question_encoder_last_hidden_state)
                    context_input_ids = context_input_ids.to(input_ids)
                    context_attention_mask = context_attention_mask.to(input_ids)

                    # compute doc_scores
                    doc_scores = torch.bmm(
                        question_encoder_last_hidden_state.unsqueeze(1), retrieved_doc_embeds.transpose(1, 2)
                    ).squeeze(1)
            else:
                assert context_input_ids is not None, (
                    "Make sure that `context_input_ids` are passed, if no `retriever` is set. Alternatively, you can"
                    " set a retriever using the `set_retriever(...)` function."
                )
                assert context_attention_mask is not None, (
                    "Make sure that `context_attention_mask` are passed, if no `retriever` is set. Alternatively, you"
                    " can set a retriever using the `set_retriever(...)` function."
                )
                assert doc_scores is not None, (
                    "Make sure that `doc_scores` are passed, if no `retriever` is set. Alternatively, you can set a"
                    " retriever using the `set_retriever(...)` function."
                )

        assert doc_scores is not None, (
            "Make sure that `doc_scores` are passed when passing `encoder_outputs` to the forward function."
        )

        assert (doc_scores.shape[1] % n_docs) == 0, (
            f" The first dimension of `context_input_ids` should be a multiple of `n_docs`={n_docs}, but is"
            f" {context_input_ids.shape[0]}."
        )

        # Decoder input without context documents
        if decoder_input_ids is not None:
            decoder_input_ids = decoder_input_ids.repeat_interleave(n_docs, dim=0)

        if decoder_attention_mask is not None:
            decoder_attention_mask = decoder_attention_mask.repeat_interleave(n_docs, dim=0)

        gen_outputs = self.generator(
            input_ids=context_input_ids,
            attention_mask=context_attention_mask,
            encoder_outputs=encoder_outputs,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            past_key_values=past_key_values,
            use_cache=use_cache,
            output_attentions=output_attentions,
            return_dict=True,
        )

        if not has_to_retrieve:
            question_encoder_last_hidden_state = None
            question_enc_hidden_states = None
            question_enc_attentions = None
            retrieved_doc_embeds = None
            retrieved_doc_ids = None
        else:
            question_enc_hidden_states = question_enc_outputs.hidden_states
            question_enc_attentions = question_enc_outputs.attentions

        if not has_to_retrieve or not output_retrieved:
            # don't output retrieved docs
            context_input_ids = (None,)
            context_attention_mask = None
            retrieved_doc_embeds = None
            retrieved_doc_ids = None

        return RetrievAugLMOutput(
            logits=gen_outputs.logits,
            doc_scores=doc_scores,
            past_key_values=gen_outputs.past_key_values,
            context_input_ids=context_input_ids,
            context_attention_mask=context_attention_mask,
            retrieved_doc_embeds=retrieved_doc_embeds,
            retrieved_doc_ids=retrieved_doc_ids,
            question_encoder_last_hidden_state=question_encoder_last_hidden_state,
            question_enc_hidden_states=question_enc_hidden_states,
            question_enc_attentions=question_enc_attentions,
            generator_enc_last_hidden_state=gen_outputs.encoder_last_hidden_state,
            generator_enc_hidden_states=gen_outputs.encoder_hidden_states,
            generator_enc_attentions=gen_outputs.encoder_attentions,
            generator_dec_hidden_states=gen_outputs.decoder_hidden_states,
            generator_dec_attentions=gen_outputs.decoder_attentions,
            generator_cross_attentions=gen_outputs.cross_attentions,
        )