def forward(
        self,
        input_ids: torch.Tensor | None = None,
        pixel_values_videos: torch.Tensor | None = None,
        input_values: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        padding_mask_videos: torch.Tensor | None = None,
        padding_mask: torch.Tensor | None = None,
        return_loss=False,
        **kwargs,
    ) -> PeAudioVideoOutput:
        if sum([input_ids is not None, pixel_values_videos is not None, input_values is not None]) < 2:
            raise ValueError("At least two of input_ids, pixel_values_videos, or input_values must be provided")

        if pixel_values_videos is None:
            outputs = self.audio_model(
                input_ids=input_ids,
                input_values=input_values,
                attention_mask=attention_mask,
                padding_mask=padding_mask,
                return_dict=True,
            )
            audio_plus_text_embeds = torch.cat(
                [outputs.audio_outputs.pooler_output, outputs.text_outputs.hidden_states[-1][:, 0]], dim=-1
            )
            audio_plus_text_embeds = self.audio_plus_text_head(audio_plus_text_embeds)
            return PeAudioVideoOutput(audio_plus_text_embeds=audio_plus_text_embeds, **outputs)

        if input_values is None:
            outputs = self.video_model(
                input_ids=input_ids,
                pixel_values_videos=pixel_values_videos,
                attention_mask=attention_mask,
                padding_mask_videos=padding_mask_videos,
                return_dict=True,
            )
            video_plus_text_embeds = torch.cat(
                [outputs.video_outputs.pooler_output, outputs.text_outputs.hidden_states[-1][:, 0]], dim=-1
            )
            video_plus_text_embeds = self.video_plus_text_head(video_plus_text_embeds)
            return PeAudioVideoOutput(video_plus_text_embeds=video_plus_text_embeds, **outputs)

        audio_video_outputs = self.audio_video_encoder(
            input_values=input_values,
            pixel_values_videos=pixel_values_videos,
            padding_mask=padding_mask,
            padding_mask_videos=padding_mask_videos,
            **kwargs,
        )
        audio_embeds = audio_video_outputs.audio_model_output.pooler_output
        video_embeds = audio_video_outputs.video_model_output.pooler_output
        audio_video_embeds = audio_video_outputs.pooler_output

        audio_embeds = self.audio_model.audio_head(audio_embeds)
        video_embeds = self.video_model.video_head(video_embeds)
        audio_video_embeds = self.audio_video_head(audio_video_embeds)
        logits_audio_video = audio_embeds @ video_embeds.T
        logits_audio_video = logits_audio_video * self.audio_video_logit_scale + self.audio_video_logit_bias
        audio_video_loss = self._contrastive_loss(logits_audio_video) if return_loss else None

        if input_ids is None:
            return PeAudioVideoOutput(
                logits_audio_video=logits_audio_video,
                audio_embeds=audio_embeds,
                video_embeds=video_embeds,
                audio_video_embeds=audio_video_embeds,
                loss=audio_video_loss,
                audio_video_loss=audio_video_loss,
            )

        kwargs["output_hidden_states"] = True
        text_outputs = self.text_model(input_ids=input_ids, attention_mask=attention_mask, **kwargs)
        text_embeds = text_outputs.hidden_states[-1][:, 0]
        audio_plus_text_embeds = torch.cat([audio_video_outputs.audio_model_output.pooler_output, text_embeds], dim=-1)
        video_plus_text_embeds = torch.cat([audio_video_outputs.video_model_output.pooler_output, text_embeds], dim=-1)

        text_audio_embeds = self.audio_model.text_audio_head(text_embeds)
        text_video_embeds = self.video_model.text_video_head(text_embeds)
        text_audio_video_embeds = self.text_audio_video_head(text_embeds)
        audio_plus_text_embeds = self.audio_plus_text_head(audio_plus_text_embeds)
        video_plus_text_embeds = self.video_plus_text_head(video_plus_text_embeds)

        logits_audio_text = audio_embeds @ text_audio_embeds.T
        logits_video_text = video_embeds @ text_video_embeds.T
        logits_audio_video_text = audio_video_embeds @ text_audio_video_embeds.T

        logits_audio_plus_text_video = audio_plus_text_embeds @ video_embeds.T
        logits_video_plus_text_audio = video_plus_text_embeds @ audio_embeds.T

        logits_audio_text = (
            logits_audio_text * self.audio_model.text_audio_logit_scale + self.audio_model.text_audio_logit_bias
        )
        logits_video_text = (
            logits_video_text * self.video_model.text_video_logit_scale + self.video_model.text_video_logit_bias
        )
        logits_audio_video_text = (
            logits_audio_video_text * self.text_audio_video_logit_scale + self.text_audio_video_logit_bias
        )

        logits_audio_plus_text_video = (
            logits_audio_plus_text_video * self.audio_plus_text_logit_scale + self.audio_plus_text_logit_bias
        )
        logits_video_plus_text_audio = (
            logits_video_plus_text_audio * self.video_plus_text_logit_scale + self.video_plus_text_logit_bias
        )

        if return_loss:
            audio_text_loss = self._contrastive_loss(logits_audio_text)
            video_text_loss = self._contrastive_loss(logits_video_text)
            audio_video_text_loss = self._contrastive_loss(logits_audio_video_text)
            audio_plus_text_video_loss = self._contrastive_loss(logits_audio_plus_text_video)
            video_plus_text_audio_loss = self._contrastive_loss(logits_video_plus_text_audio)
            loss = (
                audio_video_text_loss
                + audio_text_loss
                + video_text_loss
                + audio_video_loss
                + audio_plus_text_video_loss
                + video_plus_text_audio_loss
            )

        return PeAudioVideoOutput(
            # embeddings
            audio_embeds=audio_embeds,
            video_embeds=video_embeds,
            audio_video_embeds=audio_video_embeds,
            text_audio_embeds=text_audio_embeds,
            text_video_embeds=text_video_embeds,
            text_audio_video_embeds=text_audio_video_embeds,
            audio_plus_text_embeds=audio_plus_text_embeds,
            video_plus_text_embeds=video_plus_text_embeds,
            # model outputs
            text_outputs=text_outputs,
            audio_outputs=audio_video_outputs.audio_model_output,
            video_outputs=audio_video_outputs.video_model_output,
            audio_video_outputs=audio_video_outputs,
            # logits
            logits_audio_text=logits_audio_text,
            logits_video_text=logits_video_text,
            logits_audio_video=logits_audio_video,
            logits_audio_video_text=logits_audio_video_text,
            logits_audio_plus_text_video=logits_audio_plus_text_video,
            logits_video_plus_text_audio=logits_video_plus_text_audio,
            # losses
            audio_text_loss=audio_text_loss if return_loss else None,
            video_text_loss=video_text_loss if return_loss else None,
            audio_video_loss=audio_video_loss if return_loss else None,
            audio_video_text_loss=audio_video_text_loss if return_loss else None,
            audio_plus_text_video_loss=audio_plus_text_video_loss if return_loss else None,
            video_plus_text_audio_loss=video_plus_text_audio_loss if return_loss else None,
            loss=loss if return_loss else None,
        )