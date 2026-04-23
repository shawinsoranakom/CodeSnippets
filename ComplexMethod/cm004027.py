def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        encoder_outputs: tuple[tuple[torch.Tensor]] | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.BoolTensor | None = None,
        past_key_values: Cache | None = None,
        context_input_ids: torch.LongTensor | None = None,
        context_attention_mask: torch.LongTensor | None = None,
        doc_scores: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        output_retrieved: bool | None = None,
        do_marginalize: bool | None = None,
        reduce_loss: bool | None = None,
        labels: torch.LongTensor | None = None,
        n_docs: int | None = None,
        **kwargs,  # needs kwargs for generation
    ) -> RetrievAugLMMarginOutput:
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
        context_input_ids (`torch.LongTensor` of shape `(batch_size * config.n_docs, config.max_combined_length)`, *optional*, returned when *output_retrieved=True*):
            Input IDs post-processed from the retrieved documents and the question encoder `input_ids` by the
            retriever. If the model was not initialized with a `retriever` ``context_input_ids` has to be provided to
            the forward pass. `context_input_ids` are returned by [`~RagRetriever.__call__`].
        context_attention_mask (`torch.LongTensor` of shape `(batch_size * config.n_docs, config.max_combined_length)`,*optional*, returned when *output_retrieved=True*):
            Attention mask post-processed from the retrieved documents and the question encoder `input_ids` by the
            retriever. If the model has is not initialized with a `retriever` `context_attention_mask` has to be
            provided to the forward pass. `context_attention_mask` are returned by [`~RagRetriever.__call__`].
        doc_scores (`torch.FloatTensor` of shape `(batch_size, config.n_docs)`):
            Score between each retrieved document embeddings (see `retrieved_doc_embeds`) and
            `question_encoder_last_hidden_state`. If the model has is not initialized with a `retriever` `doc_scores`
            has to be provided to the forward pass. `doc_scores` can be computed via
            `question_encoder_last_hidden_state` and `retrieved_doc_embeds`, see examples for more information.
        output_retrieved (`bool`, *optional*):
            Whether or not to return the `retrieved_doc_embeds`, `retrieved_doc_ids`, `context_input_ids` and
            `context_attention_mask`. See returned tensors for more detail.
        do_marginalize (`bool`, *optional*):
            If `True`, the logits are marginalized over all documents by making use of
            `torch.nn.functional.log_softmax`.
        reduce_loss (`bool`, *optional*):
            Only relevant if `labels` is passed. If `True`, the NLL loss is reduced using the `torch.Tensor.sum`
            operation.
        n_docs (`int`, *optional*):
            The number of documents to retrieve.

        Example:

        ```python
        >>> from transformers import AutoTokenizer, RagRetriever, RagTokenForGeneration
        >>> import torch

        >>> tokenizer = AutoTokenizer.from_pretrained("facebook/rag-token-nq")
        >>> retriever = RagRetriever.from_pretrained(
        ...     "facebook/rag-token-nq", index_name="exact", use_dummy_dataset=True
        ... )
        >>> # initialize with RagRetriever to do everything in one forward call
        >>> model = RagTokenForGeneration.from_pretrained("facebook/rag-token-nq", retriever=retriever)

        >>> inputs = tokenizer("How many people live in Paris?", return_tensors="pt")
        >>> targets = tokenizer(text_target="In Paris, there are 10 million people.", return_tensors="pt")
        >>> input_ids = inputs["input_ids"]
        >>> labels = targets["input_ids"]
        >>> outputs = model(input_ids=input_ids, labels=labels)

        >>> # or use retriever separately
        >>> model = RagTokenForGeneration.from_pretrained("facebook/rag-token-nq", use_dummy_dataset=True)
        >>> # 1. Encode
        >>> question_hidden_states = model.question_encoder(input_ids)[0]
        >>> # 2. Retrieve
        >>> docs_dict = retriever(input_ids.numpy(), question_hidden_states.detach().numpy(), return_tensors="pt")
        >>> doc_scores = torch.bmm(
        ...     question_hidden_states.unsqueeze(1), docs_dict["retrieved_doc_embeds"].float().transpose(1, 2)
        ... ).squeeze(1)
        >>> # 3. Forward to generator
        >>> outputs = model(
        ...     context_input_ids=docs_dict["context_input_ids"],
        ...     context_attention_mask=docs_dict["context_attention_mask"],
        ...     doc_scores=doc_scores,
        ...     decoder_input_ids=labels,
        ... )

        >>> # or directly generate
        >>> generated = model.generate(
        ...     context_input_ids=docs_dict["context_input_ids"],
        ...     context_attention_mask=docs_dict["context_attention_mask"],
        ...     doc_scores=doc_scores,
        ... )
        >>> generated_string = tokenizer.batch_decode(generated, skip_special_tokens=True)
        ```"""
        n_docs = n_docs if n_docs is not None else self.config.n_docs
        do_marginalize = do_marginalize if do_marginalize is not None else self.config.do_marginalize
        reduce_loss = reduce_loss if reduce_loss is not None else self.config.reduce_loss

        if labels is not None:
            if decoder_input_ids is None:
                decoder_input_ids = labels
            use_cache = False

        outputs = self.rag(
            input_ids=input_ids,
            attention_mask=attention_mask,
            encoder_outputs=encoder_outputs,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            context_input_ids=context_input_ids,
            context_attention_mask=context_attention_mask,
            doc_scores=doc_scores,
            past_key_values=past_key_values,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            output_retrieved=output_retrieved,
            n_docs=n_docs,
        )

        loss = None
        logits = outputs.logits
        if labels is not None:
            assert decoder_input_ids is not None
            loss = self.get_nll(
                outputs.logits,
                outputs.doc_scores,
                labels,
                reduce_loss=reduce_loss,
                epsilon=self.config.label_smoothing,
                n_docs=n_docs,
            )

        if do_marginalize:
            logits = self.marginalize(logits, outputs.doc_scores, n_docs)

        return RetrievAugLMMarginOutput(
            loss=loss,
            logits=logits,
            doc_scores=outputs.doc_scores,
            past_key_values=outputs.past_key_values,
            context_input_ids=outputs.context_input_ids,
            context_attention_mask=outputs.context_attention_mask,
            retrieved_doc_embeds=outputs.retrieved_doc_embeds,
            retrieved_doc_ids=outputs.retrieved_doc_ids,
            question_encoder_last_hidden_state=outputs.question_encoder_last_hidden_state,
            question_enc_hidden_states=outputs.question_enc_hidden_states,
            question_enc_attentions=outputs.question_enc_attentions,
            generator_enc_last_hidden_state=outputs.generator_enc_last_hidden_state,
            generator_enc_hidden_states=outputs.generator_enc_hidden_states,
            generator_enc_attentions=outputs.generator_enc_attentions,
            generator_dec_hidden_states=outputs.generator_dec_hidden_states,
            generator_dec_attentions=outputs.generator_dec_attentions,
            generator_cross_attentions=outputs.generator_cross_attentions,
        )