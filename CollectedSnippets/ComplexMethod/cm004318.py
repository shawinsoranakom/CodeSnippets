def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        table_mask: torch.LongTensor | None = None,
        labels: torch.LongTensor | None = None,
        aggregation_labels: torch.LongTensor | None = None,
        float_answer: torch.FloatTensor | None = None,
        numeric_values: torch.FloatTensor | None = None,
        numeric_values_scale: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | TableQuestionAnsweringOutput:
        r"""
        token_type_ids (`torch.LongTensor` of shape `(batch_size, sequence_length, 7)`, *optional*):
            Token indices that encode tabular structure. Indices can be obtained using [`AutoTokenizer`]. See this
            class for more info.

            [What are token type IDs?](../glossary#token-type-ids)
        position_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. If
            `reset_position_index_per_cell` of [`TapasConfig`] is set to `True`, relative position embeddings will be
            used. Selected in the range `[0, config.max_position_embeddings - 1]`.

            [What are position IDs?](../glossary#position-ids)
        table_mask (`torch.LongTensor` of shape `(batch_size, seq_length)`, *optional*):
            Mask for the table. Indicates which tokens belong to the table (1). Question tokens, table headers and
            padding are 0.
        labels (`torch.LongTensor` of shape `(batch_size, seq_length)`, *optional*):
            Labels per token for computing the hierarchical cell selection loss. This encodes the positions of the
            answer appearing in the table. Can be obtained using [`AutoTokenizer`].

            - 1 for tokens that are **part of the answer**,
            - 0 for tokens that are **not part of the answer**.
        aggregation_labels (`torch.LongTensor` of shape `(batch_size, )`, *optional*):
            Aggregation function index for every example in the batch for computing the aggregation loss. Indices
            should be in `[0, ..., config.num_aggregation_labels - 1]`. Only required in case of strong supervision for
            aggregation (WikiSQL-supervised).
        float_answer (`torch.FloatTensor` of shape `(batch_size, )`, *optional*):
            Float answer for every example in the batch. Set to *float('nan')* for cell selection questions. Only
            required in case of weak supervision (WTQ) to calculate the aggregate mask and regression loss.
        numeric_values (`torch.FloatTensor` of shape `(batch_size, seq_length)`, *optional*):
            Numeric values of every token, NaN for tokens which are not numeric values. Can be obtained using
            [`AutoTokenizer`]. Only required in case of weak supervision for aggregation (WTQ) to calculate the
            regression loss.
        numeric_values_scale (`torch.FloatTensor` of shape `(batch_size, seq_length)`, *optional*):
            Scale of the numeric values of every token. Can be obtained using [`AutoTokenizer`]. Only required in case
            of weak supervision for aggregation (WTQ) to calculate the regression loss.

        Examples:

        ```python
        >>> from transformers import AutoTokenizer, TapasForQuestionAnswering
        >>> import pandas as pd

        >>> tokenizer = AutoTokenizer.from_pretrained("google/tapas-base-finetuned-wtq")
        >>> model = TapasForQuestionAnswering.from_pretrained("google/tapas-base-finetuned-wtq")

        >>> data = {
        ...     "Actors": ["Brad Pitt", "Leonardo Di Caprio", "George Clooney"],
        ...     "Age": ["56", "45", "59"],
        ...     "Number of movies": ["87", "53", "69"],
        ... }
        >>> table = pd.DataFrame.from_dict(data)
        >>> queries = ["How many movies has George Clooney played in?", "How old is Brad Pitt?"]

        >>> inputs = tokenizer(table=table, queries=queries, padding="max_length", return_tensors="pt")
        >>> outputs = model(**inputs)

        >>> logits = outputs.logits
        >>> logits_aggregation = outputs.logits_aggregation
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.tapas(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]
        pooled_output = outputs[1]

        sequence_output = self.dropout(sequence_output)

        if input_ids is not None:
            input_shape = input_ids.size()
        else:
            input_shape = inputs_embeds.size()[:-1]

        device = input_ids.device if input_ids is not None else inputs_embeds.device

        # Construct indices for the table.
        if token_type_ids is None:
            token_type_ids = torch.zeros(
                (*input_shape, len(self.config.type_vocab_sizes)), dtype=torch.long, device=device
            )

        token_types = [
            "segment_ids",
            "column_ids",
            "row_ids",
            "prev_labels",
            "column_ranks",
            "inv_column_ranks",
            "numeric_relations",
        ]

        row_ids = token_type_ids[:, :, token_types.index("row_ids")]
        column_ids = token_type_ids[:, :, token_types.index("column_ids")]

        row_index = IndexMap(
            indices=torch.min(row_ids, torch.as_tensor(self.config.max_num_rows - 1, device=row_ids.device)),
            num_segments=self.config.max_num_rows,
            batch_dims=1,
        )
        col_index = IndexMap(
            indices=torch.min(column_ids, torch.as_tensor(self.config.max_num_columns - 1, device=column_ids.device)),
            num_segments=self.config.max_num_columns,
            batch_dims=1,
        )
        cell_index = ProductIndexMap(row_index, col_index)

        # Masks.
        input_shape = input_ids.size() if input_ids is not None else inputs_embeds.size()[:-1]
        device = input_ids.device if input_ids is not None else inputs_embeds.device
        if attention_mask is None:
            attention_mask = torch.ones(input_shape, device=device)
        # Table cells only, without question tokens and table headers.
        if table_mask is None:
            table_mask = torch.where(row_ids > 0, torch.ones_like(row_ids), torch.zeros_like(row_ids))
        # torch.FloatTensor[batch_size, seq_length]
        input_mask_float = attention_mask.to(device=device, dtype=torch.float)
        table_mask_float = table_mask.to(device=device, dtype=torch.float)
        # Mask for cells that exist in the table (i.e. that are not padding).
        cell_mask, _ = reduce_mean(input_mask_float, cell_index)

        # Compute logits per token. These are used to select individual cells.
        logits = compute_token_logits(sequence_output, self.config.temperature, self.output_weights, self.output_bias)

        # Compute logits per column. These are used to select a column.
        column_logits = None
        if self.config.select_one_column:
            column_logits = compute_column_logits(
                sequence_output,
                self.column_output_weights,
                self.column_output_bias,
                cell_index,
                cell_mask,
                self.config.allow_empty_column_selection,
            )

        # Aggregation logits
        logits_aggregation = None
        if self.config.num_aggregation_labels > 0:
            logits_aggregation = self.aggregation_classifier(pooled_output)

        # Total loss calculation
        total_loss = 0.0
        calculate_loss = False
        if labels is not None:
            calculate_loss = True
            is_supervised = not self.config.num_aggregation_labels > 0 or not self.config.use_answer_as_supervision

            # Semi-supervised cell selection in case of no aggregation:
            # If the answer (the denotation) appears directly in the table we might
            # select the answer without applying any aggregation function. There are
            # some ambiguous cases, see utils._calculate_aggregate_mask for more info.
            # `aggregate_mask` is 1 for examples where we chose to aggregate and 0
            #  for examples where we chose to select the answer directly.
            # `labels` encodes the positions of the answer appearing in the table.
            if is_supervised:
                aggregate_mask = None
            else:
                if float_answer is not None:
                    assert labels.shape[0] == float_answer.shape[0], (
                        "Make sure the answers are a FloatTensor of shape (batch_size,)"
                    )
                    # <float32>[batch_size]
                    aggregate_mask = _calculate_aggregate_mask(
                        float_answer,
                        pooled_output,
                        self.config.cell_selection_preference,
                        labels,
                        self.aggregation_classifier,
                    )
                else:
                    raise ValueError("You have to specify float answers in order to calculate the aggregate mask")

            # Cell selection log-likelihood
            if self.config.average_logits_per_cell:
                logits_per_cell, _ = reduce_mean(logits, cell_index)
                logits = gather(logits_per_cell, cell_index)
            dist_per_token = torch.distributions.Bernoulli(logits=logits)

            # Compute cell selection loss per example.
            selection_loss_per_example = None
            if not self.config.select_one_column:
                weight = torch.where(
                    labels == 0,
                    torch.ones_like(labels, dtype=torch.float32),
                    self.config.positive_label_weight * torch.ones_like(labels, dtype=torch.float32),
                )
                selection_loss_per_token = -dist_per_token.log_prob(labels) * weight
                selection_loss_per_example = torch.sum(selection_loss_per_token * input_mask_float, dim=1) / (
                    torch.sum(input_mask_float, dim=1) + EPSILON_ZERO_DIVISION
                )
            else:
                selection_loss_per_example, logits = _single_column_cell_selection_loss(
                    logits, column_logits, labels, cell_index, col_index, cell_mask
                )
                dist_per_token = torch.distributions.Bernoulli(logits=logits)

            # Supervised cell selection
            if self.config.disable_per_token_loss:
                pass
            elif is_supervised:
                total_loss += torch.mean(selection_loss_per_example)
            else:
                # For the not supervised case, do not assign loss for cell selection
                total_loss += torch.mean(selection_loss_per_example * (1.0 - aggregate_mask))

            # Semi-supervised regression loss and supervised loss for aggregations
            if self.config.num_aggregation_labels > 0:
                if is_supervised:
                    # Note that `aggregate_mask` is None if the setting is supervised.
                    if aggregation_labels is not None:
                        assert labels.shape[0] == aggregation_labels.shape[0], (
                            "Make sure the aggregation labels are a LongTensor of shape (batch_size,)"
                        )
                        per_example_additional_loss = _calculate_aggregation_loss(
                            logits_aggregation,
                            aggregate_mask,
                            aggregation_labels,
                            self.config.use_answer_as_supervision,
                            self.config.num_aggregation_labels,
                            self.config.aggregation_loss_weight,
                        )
                    else:
                        raise ValueError(
                            "You have to specify aggregation labels in order to calculate the aggregation loss"
                        )
                else:
                    # Set aggregation labels to zeros
                    aggregation_labels = torch.zeros(labels.shape[0], dtype=torch.long, device=labels.device)
                    per_example_additional_loss = _calculate_aggregation_loss(
                        logits_aggregation,
                        aggregate_mask,
                        aggregation_labels,
                        self.config.use_answer_as_supervision,
                        self.config.num_aggregation_labels,
                        self.config.aggregation_loss_weight,
                    )

                if self.config.use_answer_as_supervision:
                    if numeric_values is not None and numeric_values_scale is not None:
                        assert numeric_values.shape == numeric_values_scale.shape
                        # Add regression loss for numeric answers which require aggregation.
                        answer_loss, large_answer_loss_mask = _calculate_regression_loss(
                            float_answer,
                            aggregate_mask,
                            dist_per_token,
                            numeric_values,
                            numeric_values_scale,
                            table_mask_float,
                            logits_aggregation,
                            self.config,
                        )
                        per_example_additional_loss += answer_loss
                        # Zero loss for examples with answer_loss > cutoff.
                        per_example_additional_loss *= large_answer_loss_mask
                    else:
                        raise ValueError(
                            "You have to specify numeric values and numeric values scale in order to calculate the"
                            " regression loss"
                        )

                total_loss += torch.mean(per_example_additional_loss)

        else:
            # if no label ids are provided, set them to zeros in order to properly compute logits
            labels = torch.zeros_like(logits)
            _, logits = _single_column_cell_selection_loss(
                logits, column_logits, labels, cell_index, col_index, cell_mask
            )
        if not return_dict:
            output = (logits, logits_aggregation) + outputs[2:]
            return ((total_loss,) + output) if calculate_loss else output

        return TableQuestionAnsweringOutput(
            loss=total_loss if calculate_loss else None,
            logits=logits,
            logits_aggregation=logits_aggregation,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )