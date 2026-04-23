def extra_conds(self, **kwargs):
        out = super().extra_conds(**kwargs)
        device = kwargs["device"]
        noise = kwargs["noise"]

        cross_attn = kwargs.get("cross_attn", None)
        if cross_attn is not None:
            if torch.count_nonzero(cross_attn) == 0:
                out['replace_with_null_embeds'] = comfy.conds.CONDConstant(True)
            out['c_crossattn'] = comfy.conds.CONDRegular(cross_attn)

        conditioning_lyrics = kwargs.get("conditioning_lyrics", None)
        if cross_attn is not None:
            out['lyric_embed'] = comfy.conds.CONDRegular(conditioning_lyrics)

        refer_audio = kwargs.get("reference_audio_timbre_latents", None)
        if refer_audio is None or len(refer_audio) == 0:
            refer_audio = comfy.ldm.ace.ace_step15.get_silence_latent(noise.shape[2], device)
            pass_audio_codes = True
        else:
            refer_audio = refer_audio[-1][:, :, :noise.shape[2]]
            out['is_covers'] = comfy.conds.CONDConstant(True)
            pass_audio_codes = False

        if pass_audio_codes:
            audio_codes = kwargs.get("audio_codes", None)
            if audio_codes is not None:
                out['audio_codes'] = comfy.conds.CONDRegular(torch.tensor(audio_codes, device=device))
                refer_audio = refer_audio[:, :, :750]
            else:
                out['is_covers'] = comfy.conds.CONDConstant(False)

        if refer_audio.shape[2] < noise.shape[2]:
            pad = comfy.ldm.ace.ace_step15.get_silence_latent(noise.shape[2], device)
            refer_audio = torch.cat([refer_audio.to(pad), pad[:, :, refer_audio.shape[2]:]], dim=2)

        out['refer_audio'] = comfy.conds.CONDRegular(refer_audio)
        return out