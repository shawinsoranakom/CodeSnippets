def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        masking_pattern: torch.Tensor | None = None,
        num_recycles: int | None = None,
        output_hidden_states: bool | None = False,
        **kwargs,
    ) -> EsmForProteinFoldingOutput:
        r"""
        masking_pattern (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Locations of tokens to mask during training as a form of regularization. Mask values selected in `[0, 1]`.
        num_recycles (`int`, *optional*, defaults to `None`):
            Number of times to recycle the input sequence. If `None`, defaults to `config.num_recycles`. "Recycling"
            consists of passing the output of the folding trunk back in as input to the trunk. During training, the
            number of recycles should vary with each batch, to ensure that the model learns to output valid predictions
            after each recycle. During inference, num_recycles should be set to the highest value that the model was
            trained with for maximum accuracy. Accordingly, when this value is set to `None`, config.max_recycles is
            used.

        Example:

        ```python
        >>> from transformers import AutoTokenizer, EsmForProteinFolding

        >>> model = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1")
        >>> tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
        >>> inputs = tokenizer(["MLKNVQVQLV"], return_tensors="pt", add_special_tokens=False)  # A tiny random peptide
        >>> outputs = model(**inputs)
        >>> folded_positions = outputs.positions
        ```

        """
        cfg = self.config.esmfold_config

        aa = input_ids  # B x L
        B = aa.shape[0]
        L = aa.shape[1]
        device = input_ids.device
        if attention_mask is None:
            attention_mask = torch.ones_like(aa, device=device)
        if position_ids is None:
            position_ids = torch.arange(L, device=device).expand_as(input_ids)

        # === ESM ===
        esmaa = self.af2_idx_to_esm_idx(aa, attention_mask)

        if masking_pattern is not None:
            masked_aa, esmaa, mlm_targets = self.bert_mask(aa, esmaa, attention_mask, masking_pattern)
        else:
            masked_aa = aa
            mlm_targets = None

        # We get sequence and pair representations from whatever version of ESM /
        # configuration we are using. The sequence representation esm_s is always
        # present. The pair embedding esm_z may be present depending on the
        # configuration of the model. If esm_z is not used by the model then it
        # is returned as None here.
        esm_s = self.compute_language_model_representations(esmaa)

        # Convert esm_s and esm_z, if present, to the precision used by the trunk and
        # the structure module. These tensors may be a lower precision if, for example,
        # we're running the language model in fp16 precision.
        esm_s = esm_s.to(self.esm_s_combine.dtype)

        if cfg.esm_ablate_sequence:
            esm_s = esm_s * 0

        esm_s = esm_s.detach()

        # === preprocessing ===
        esm_s = (self.esm_s_combine.softmax(0).unsqueeze(0) @ esm_s).squeeze(2)
        s_s_0 = self.esm_s_mlp(esm_s)

        s_z_0 = s_s_0.new_zeros(B, L, L, cfg.trunk.pairwise_state_dim)

        if self.config.esmfold_config.embed_aa:
            s_s_0 += self.embedding(masked_aa)

        structure: dict = self.trunk(s_s_0, s_z_0, aa, position_ids, attention_mask, no_recycles=num_recycles)
        # Documenting what we expect:
        structure = {
            k: v
            for k, v in structure.items()
            if k
            in [
                "s_z",
                "s_s",
                "frames",
                "sidechain_frames",
                "unnormalized_angles",
                "angles",
                "positions",
                "states",
            ]
        }

        # Add BERT mask for the loss to use, if available.
        if mlm_targets:
            structure["mlm_targets"] = mlm_targets

        disto_logits = self.distogram_head(structure["s_z"])
        disto_logits = (disto_logits + disto_logits.transpose(1, 2)) / 2
        structure["distogram_logits"] = disto_logits

        lm_logits = self.lm_head(structure["s_s"])
        structure["lm_logits"] = lm_logits

        structure["aatype"] = aa
        make_atom14_masks(structure)
        # Of course, this doesn't respect the true mask because it doesn't know about it...
        # We're not going to properly mask change of index tensors:
        #    "residx_atom14_to_atom37",
        #    "residx_atom37_to_atom14",
        for k in [
            "atom14_atom_exists",
            "atom37_atom_exists",
        ]:
            structure[k] *= attention_mask.unsqueeze(-1)
        structure["residue_index"] = position_ids

        lddt_head = self.lddt_head(structure["states"]).reshape(structure["states"].shape[0], B, L, -1, self.lddt_bins)
        structure["lddt_head"] = lddt_head
        plddt = categorical_lddt(lddt_head[-1], bins=self.lddt_bins)
        structure["plddt"] = plddt

        ptm_logits = self.ptm_head(structure["s_z"])
        structure["ptm_logits"] = ptm_logits
        structure["ptm"] = compute_tm(ptm_logits, max_bin=31, no_bins=self.distogram_bins)
        structure.update(compute_predicted_aligned_error(ptm_logits, max_bin=31, no_bins=self.distogram_bins))

        return EsmForProteinFoldingOutput(**structure)