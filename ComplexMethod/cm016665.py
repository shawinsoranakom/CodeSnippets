def forward(
        self, x: Tuple[torch.Tensor, torch.Tensor], v_context=None, a_context=None, attention_mask=None, v_timestep=None, a_timestep=None,
        v_pe=None, a_pe=None, v_cross_pe=None, a_cross_pe=None, v_cross_scale_shift_timestep=None, a_cross_scale_shift_timestep=None,
        v_cross_gate_timestep=None, a_cross_gate_timestep=None, transformer_options=None, self_attention_mask=None,
        v_prompt_timestep=None, a_prompt_timestep=None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        run_vx = transformer_options.get("run_vx", True)
        run_ax = transformer_options.get("run_ax", True)

        vx, ax = x
        run_ax = run_ax and ax.numel() > 0
        run_a2v = run_vx and transformer_options.get("a2v_cross_attn", True) and ax.numel() > 0
        run_v2a = run_ax and transformer_options.get("v2a_cross_attn", True)

        # video
        if run_vx:
            # video self-attention
            vshift_msa, vscale_msa = (self.get_ada_values(self.scale_shift_table, vx.shape[0], v_timestep, slice(0, 2)))
            norm_vx = comfy.ldm.common_dit.rms_norm(vx) * (1 + vscale_msa) + vshift_msa
            del vshift_msa, vscale_msa
            attn1_out = self.attn1(norm_vx, pe=v_pe, mask=self_attention_mask, transformer_options=transformer_options)
            del norm_vx
            # video cross-attention
            vgate_msa = self.get_ada_values(self.scale_shift_table, vx.shape[0], v_timestep, slice(2, 3))[0]
            vx.addcmul_(attn1_out, vgate_msa)
            del vgate_msa, attn1_out
            vx.add_(self._apply_text_cross_attention(
                vx, v_context, self.attn2, self.scale_shift_table,
                getattr(self, 'prompt_scale_shift_table', None),
                v_timestep, v_prompt_timestep, attention_mask, transformer_options,)
            )

        # audio
        if run_ax:
            # audio self-attention
            ashift_msa, ascale_msa = (self.get_ada_values(self.audio_scale_shift_table, ax.shape[0], a_timestep, slice(0, 2)))
            norm_ax = comfy.ldm.common_dit.rms_norm(ax) * (1 + ascale_msa) + ashift_msa
            del ashift_msa, ascale_msa
            attn1_out = self.audio_attn1(norm_ax, pe=a_pe, transformer_options=transformer_options)
            del norm_ax
            # audio cross-attention
            agate_msa = self.get_ada_values(self.audio_scale_shift_table, ax.shape[0], a_timestep, slice(2, 3))[0]
            ax.addcmul_(attn1_out, agate_msa)
            del agate_msa, attn1_out
            ax.add_(self._apply_text_cross_attention(
                ax, a_context, self.audio_attn2, self.audio_scale_shift_table,
                getattr(self, 'audio_prompt_scale_shift_table', None),
                a_timestep, a_prompt_timestep, attention_mask, transformer_options,)
            )

        # video - audio cross attention.
        if run_a2v or run_v2a:
            vx_norm3 = comfy.ldm.common_dit.rms_norm(vx)
            ax_norm3 = comfy.ldm.common_dit.rms_norm(ax)

            # audio to video cross attention
            if run_a2v:
                scale_ca_audio_hidden_states_a2v, shift_ca_audio_hidden_states_a2v = self.get_ada_values(
                    self.scale_shift_table_a2v_ca_audio[:4, :], ax.shape[0], a_cross_scale_shift_timestep)[:2]
                scale_ca_video_hidden_states_a2v_v, shift_ca_video_hidden_states_a2v_v = self.get_ada_values(
                    self.scale_shift_table_a2v_ca_video[:4, :], vx.shape[0], v_cross_scale_shift_timestep)[:2]

                vx_scaled = vx_norm3 * (1 + scale_ca_video_hidden_states_a2v_v) + shift_ca_video_hidden_states_a2v_v
                ax_scaled = ax_norm3 * (1 + scale_ca_audio_hidden_states_a2v) + shift_ca_audio_hidden_states_a2v
                del scale_ca_video_hidden_states_a2v_v, shift_ca_video_hidden_states_a2v_v, scale_ca_audio_hidden_states_a2v, shift_ca_audio_hidden_states_a2v

                a2v_out = self.audio_to_video_attn(vx_scaled, context=ax_scaled, pe=v_cross_pe, k_pe=a_cross_pe, transformer_options=transformer_options)
                del vx_scaled, ax_scaled

                gate_out_a2v = self.get_ada_values(self.scale_shift_table_a2v_ca_video[4:, :], vx.shape[0], v_cross_gate_timestep)[0]
                vx.addcmul_(a2v_out, gate_out_a2v)
                del gate_out_a2v, a2v_out

            # video to audio cross attention
            if run_v2a:
                scale_ca_audio_hidden_states_v2a, shift_ca_audio_hidden_states_v2a = self.get_ada_values(
                    self.scale_shift_table_a2v_ca_audio[:4, :], ax.shape[0], a_cross_scale_shift_timestep)[2:4]
                scale_ca_video_hidden_states_v2a, shift_ca_video_hidden_states_v2a = self.get_ada_values(
                    self.scale_shift_table_a2v_ca_video[:4, :], vx.shape[0], v_cross_scale_shift_timestep)[2:4]

                ax_scaled = ax_norm3 * (1 + scale_ca_audio_hidden_states_v2a) + shift_ca_audio_hidden_states_v2a
                vx_scaled = vx_norm3 * (1 + scale_ca_video_hidden_states_v2a) + shift_ca_video_hidden_states_v2a
                del scale_ca_video_hidden_states_v2a, shift_ca_video_hidden_states_v2a, scale_ca_audio_hidden_states_v2a, shift_ca_audio_hidden_states_v2a

                v2a_out = self.video_to_audio_attn(ax_scaled, context=vx_scaled, pe=a_cross_pe, k_pe=v_cross_pe, transformer_options=transformer_options)
                del ax_scaled, vx_scaled

                gate_out_v2a = self.get_ada_values(self.scale_shift_table_a2v_ca_audio[4:, :], ax.shape[0], a_cross_gate_timestep)[0]
                ax.addcmul_(v2a_out, gate_out_v2a)
                del gate_out_v2a, v2a_out

            del vx_norm3, ax_norm3

        # video feedforward
        if run_vx:
            vshift_mlp, vscale_mlp = self.get_ada_values(self.scale_shift_table, vx.shape[0], v_timestep, slice(3, 5))
            vx_scaled = comfy.ldm.common_dit.rms_norm(vx) * (1 + vscale_mlp) + vshift_mlp
            del vshift_mlp, vscale_mlp

            ff_out = self.ff(vx_scaled)
            del vx_scaled

            vgate_mlp = self.get_ada_values(self.scale_shift_table, vx.shape[0], v_timestep, slice(5, 6))[0]
            vx.addcmul_(ff_out, vgate_mlp)
            del vgate_mlp, ff_out

        # audio feedforward
        if run_ax:
            ashift_mlp, ascale_mlp = self.get_ada_values(self.audio_scale_shift_table, ax.shape[0], a_timestep, slice(3, 5))
            ax_scaled = comfy.ldm.common_dit.rms_norm(ax) * (1 + ascale_mlp) + ashift_mlp
            del ashift_mlp, ascale_mlp

            ff_out = self.audio_ff(ax_scaled)
            del ax_scaled

            agate_mlp = self.get_ada_values(self.audio_scale_shift_table, ax.shape[0], a_timestep, slice(5, 6))[0]
            ax.addcmul_(ff_out, agate_mlp)
            del agate_mlp, ff_out

        return vx, ax