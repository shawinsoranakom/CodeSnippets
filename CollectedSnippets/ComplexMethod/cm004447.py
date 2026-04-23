def _generate_speech(
    model: SpeechT5PreTrainedModel,
    input_values: torch.FloatTensor,
    speaker_embeddings: torch.FloatTensor | None = None,
    attention_mask: torch.LongTensor | None = None,
    threshold: float = 0.5,
    minlenratio: float = 0.0,
    maxlenratio: float = 20.0,
    vocoder: nn.Module | None = None,
    output_cross_attentions: bool = False,
    return_output_lengths: bool = False,
) -> torch.FloatTensor | tuple[torch.FloatTensor, torch.FloatTensor]:
    if speaker_embeddings is None:
        raise ValueError(
            """`speaker_embeddings` must be specified. For example, you can use a speaker embeddings by following
                    the code snippet provided in this link:
                    https://huggingface.co/datasets/Matthijs/cmu-arctic-xvectors
                    """
        )

    if attention_mask is None:
        encoder_attention_mask = 1 - (input_values == model.config.pad_token_id).int()
    else:
        encoder_attention_mask = attention_mask

    bsz = input_values.size(0)

    encoder_out = model.speecht5.encoder(
        input_values=input_values,
        attention_mask=encoder_attention_mask,
        return_dict=True,
    )

    encoder_last_hidden_state = encoder_out.last_hidden_state

    # downsample encoder attention mask
    if isinstance(model.speecht5.encoder, SpeechT5EncoderWithSpeechPrenet):
        encoder_attention_mask = model.speecht5.encoder.prenet._get_feature_vector_attention_mask(
            encoder_out[0].shape[1], encoder_attention_mask
        )

    maxlen = int(encoder_last_hidden_state.size(1) * maxlenratio / model.config.reduction_factor)
    minlen = int(encoder_last_hidden_state.size(1) * minlenratio / model.config.reduction_factor)

    # Start the output sequence with a mel spectrum that is all zeros.
    output_sequence = encoder_last_hidden_state.new_zeros(bsz, 1, model.config.num_mel_bins)

    spectrogram = []
    cross_attentions = []
    past_key_values = None
    idx = 0
    result_spectrogram = {}

    while True:
        idx += 1

        # Run the decoder prenet on the entire output sequence.
        decoder_hidden_states = model.speecht5.decoder.prenet(output_sequence, speaker_embeddings)
        # Run the decoder layers on the last element of the prenet output.
        decoder_out = model.speecht5.decoder.wrapped_decoder(
            hidden_states=decoder_hidden_states[:, -1:],
            attention_mask=None,
            encoder_hidden_states=encoder_last_hidden_state,
            encoder_attention_mask=encoder_attention_mask,
            past_key_values=past_key_values,
            use_cache=True,
            output_attentions=output_cross_attentions,
            return_dict=True,
        )

        if output_cross_attentions:
            cross_attentions.append(torch.cat(decoder_out.cross_attentions, dim=0))

        last_decoder_output = decoder_out.last_hidden_state.squeeze(1)
        past_key_values = decoder_out.past_key_values

        # Predict the new mel spectrum for this step in the sequence.
        spectrum = model.speech_decoder_postnet.feat_out(last_decoder_output)
        spectrum = spectrum.view(bsz, model.config.reduction_factor, model.config.num_mel_bins)
        spectrogram.append(spectrum)

        # Extend the output sequence with the new mel spectrum.
        new_spectrogram = spectrum[:, -1, :].view(bsz, 1, model.config.num_mel_bins)
        output_sequence = torch.cat((output_sequence, new_spectrogram), dim=1)
        # Predict the probability that this is the stop token.
        prob = torch.sigmoid(model.speech_decoder_postnet.prob_out(last_decoder_output))

        if idx < minlen:
            continue
        else:
            # If the generation loop is less than maximum length time, check the ones in the batch that have met
            # the prob threshold. Otherwise, assume all have met thresholds and fill other spectrograms for the batch.
            if idx < maxlen:
                meet_thresholds = torch.sum(prob, dim=-1) >= threshold
                meet_indexes = torch.where(meet_thresholds)[0].tolist()
            else:
                meet_indexes = range(len(prob))
            meet_indexes = [i for i in meet_indexes if i not in result_spectrogram]
            if len(meet_indexes) > 0:
                spectrograms = torch.stack(spectrogram)
                spectrograms = spectrograms.transpose(0, 1).flatten(1, 2)
                spectrograms = model.speech_decoder_postnet.postnet(spectrograms)
                for meet_index in meet_indexes:
                    result_spectrogram[meet_index] = spectrograms[meet_index]
            if len(result_spectrogram) >= bsz:
                break
    spectrograms = [result_spectrogram[i] for i in range(len(result_spectrogram))]
    if not return_output_lengths:
        spectrogram = spectrograms[0] if bsz == 1 else torch.nn.utils.rnn.pad_sequence(spectrograms, batch_first=True)
        if vocoder is not None:
            outputs = vocoder(spectrogram)
        else:
            outputs = spectrogram
        if output_cross_attentions:
            cross_attentions = torch.cat(cross_attentions, dim=2)
            if bsz > 1:
                cross_attentions = cross_attentions.view(
                    bsz, int(cross_attentions.size(0) / bsz), *cross_attentions.size()[-3:]
                )
            outputs = (outputs, cross_attentions)
    else:
        # batched return values should also include the spectrogram/waveform lengths
        spectrogram_lengths = []
        for i in range(bsz):
            spectrogram_lengths.append(spectrograms[i].size(0))
        if vocoder is None:
            spectrograms = torch.nn.utils.rnn.pad_sequence(spectrograms, batch_first=True)
            outputs = (spectrograms, spectrogram_lengths)
        else:
            waveforms = []
            spectrograms = torch.nn.utils.rnn.pad_sequence(spectrograms, batch_first=True)
            waveforms = vocoder(spectrograms)
            waveform_lengths = [int(waveforms.size(1) / max(spectrogram_lengths)) * i for i in spectrogram_lengths]
            outputs = (waveforms, waveform_lengths)
        if output_cross_attentions:
            cross_attentions = torch.cat(cross_attentions, dim=2)
            cross_attentions = cross_attentions.view(
                bsz, int(cross_attentions.size(0) / bsz), *cross_attentions.size()[-3:]
            )
            outputs = (*outputs, cross_attentions)
    return outputs