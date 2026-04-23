def forward(
        self,
        hidden_states: torch.FloatTensor,
        encoder_hidden_states: torch.FloatTensor = None,
        attention_mask: torch.FloatTensor = None,
        encoder_attention_mask: torch.FloatTensor = None,
        rotary_freqs_cis: Union[torch.Tensor, Tuple[torch.Tensor]] = None,
        rotary_freqs_cis_cross: Union[torch.Tensor, Tuple[torch.Tensor]] = None,
        temb: torch.FloatTensor = None,
        transformer_options={},
    ):

        N = hidden_states.shape[0]

        # step 1: AdaLN single
        if self.use_adaln_single:
            shift_msa, scale_msa, gate_msa, shift_mlp, scale_mlp, gate_mlp = (
                comfy.model_management.cast_to(self.scale_shift_table[None], dtype=temb.dtype, device=temb.device) + temb.reshape(N, 6, -1)
            ).chunk(6, dim=1)

        norm_hidden_states = self.norm1(hidden_states)
        if self.use_adaln_single:
            norm_hidden_states = norm_hidden_states * (1 + scale_msa) + shift_msa

        # step 2: attention
        if not self.add_cross_attention:
            attn_output, encoder_hidden_states = self.attn(
                hidden_states=norm_hidden_states,
                attention_mask=attention_mask,
                encoder_hidden_states=encoder_hidden_states,
                encoder_attention_mask=encoder_attention_mask,
                rotary_freqs_cis=rotary_freqs_cis,
                rotary_freqs_cis_cross=rotary_freqs_cis_cross,
                transformer_options=transformer_options,
            )
        else:
            attn_output, _ = self.attn(
                hidden_states=norm_hidden_states,
                attention_mask=attention_mask,
                encoder_hidden_states=None,
                encoder_attention_mask=None,
                rotary_freqs_cis=rotary_freqs_cis,
                rotary_freqs_cis_cross=None,
                transformer_options=transformer_options,
            )

        if self.use_adaln_single:
            attn_output = gate_msa * attn_output
        hidden_states = attn_output + hidden_states

        if self.add_cross_attention:
            attn_output = self.cross_attn(
                hidden_states=hidden_states,
                attention_mask=attention_mask,
                encoder_hidden_states=encoder_hidden_states,
                encoder_attention_mask=encoder_attention_mask,
                rotary_freqs_cis=rotary_freqs_cis,
                rotary_freqs_cis_cross=rotary_freqs_cis_cross,
                transformer_options=transformer_options,
            )
            hidden_states = attn_output + hidden_states

        # step 3: add norm
        norm_hidden_states = self.norm2(hidden_states)
        if self.use_adaln_single:
            norm_hidden_states = norm_hidden_states * (1 + scale_mlp) + shift_mlp

        # step 4: feed forward
        ff_output = self.ff(norm_hidden_states)
        if self.use_adaln_single:
            ff_output = gate_mlp * ff_output

        hidden_states = hidden_states + ff_output

        return hidden_states