def save_audio(
        audio: dict,
        filename_prefix: str,
        folder_type: FolderType,
        cls: type[ComfyNode] | None,
        format: str = "flac",
        quality: str = "128k",
    ) -> list[SavedResult]:
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            filename_prefix, _get_directory_by_folder_type(folder_type)
        )

        metadata = {}
        if not args.disable_metadata and cls is not None:
            if cls.hidden.prompt is not None:
                metadata["prompt"] = json.dumps(cls.hidden.prompt)
            if cls.hidden.extra_pnginfo is not None:
                for x in cls.hidden.extra_pnginfo:
                    metadata[x] = json.dumps(cls.hidden.extra_pnginfo[x])

        results = []
        for batch_number, waveform in enumerate(audio["waveform"].cpu()):
            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.{format}"
            output_path = os.path.join(full_output_folder, file)

            # Use original sample rate initially
            sample_rate = audio["sample_rate"]

            # Handle Opus sample rate requirements
            if format == "opus":
                if sample_rate > 48000:
                    sample_rate = 48000
                elif sample_rate not in AudioSaveHelper._OPUS_RATES:
                    # Find the next highest supported rate
                    for rate in sorted(AudioSaveHelper._OPUS_RATES):
                        if rate > sample_rate:
                            sample_rate = rate
                            break
                    if sample_rate not in AudioSaveHelper._OPUS_RATES:  # Fallback if still not supported
                        sample_rate = 48000

                # Resample if necessary
                if sample_rate != audio["sample_rate"]:
                    if not TORCH_AUDIO_AVAILABLE:
                        raise Exception("torchaudio is not available; cannot resample audio.")
                    waveform = torchaudio.functional.resample(waveform, audio["sample_rate"], sample_rate)

            # Create output with specified format
            output_buffer = BytesIO()
            output_container = av.open(output_buffer, mode="w", format=format)

            # Set metadata on the container
            for key, value in metadata.items():
                output_container.metadata[key] = value

            layout = "mono" if waveform.shape[0] == 1 else "stereo"
            # Set up the output stream with appropriate properties
            if format == "opus":
                out_stream = output_container.add_stream("libopus", rate=sample_rate, layout=layout)
                if quality == "64k":
                    out_stream.bit_rate = 64000
                elif quality == "96k":
                    out_stream.bit_rate = 96000
                elif quality == "128k":
                    out_stream.bit_rate = 128000
                elif quality == "192k":
                    out_stream.bit_rate = 192000
                elif quality == "320k":
                    out_stream.bit_rate = 320000
            elif format == "mp3":
                out_stream = output_container.add_stream("libmp3lame", rate=sample_rate, layout=layout)
                if quality == "V0":
                    # TODO i would really love to support V3 and V5 but there doesn't seem to be a way to set the qscale level, the property below is a bool
                    out_stream.codec_context.qscale = 1
                elif quality == "128k":
                    out_stream.bit_rate = 128000
                elif quality == "320k":
                    out_stream.bit_rate = 320000
            else:  # format == "flac":
                out_stream = output_container.add_stream("flac", rate=sample_rate, layout=layout)

            frame = av.AudioFrame.from_ndarray(
                waveform.movedim(0, 1).reshape(1, -1).float().numpy(),
                format="flt",
                layout=layout,
            )
            frame.sample_rate = sample_rate
            frame.pts = 0
            output_container.mux(out_stream.encode(frame))

            # Flush encoder
            output_container.mux(out_stream.encode(None))

            # Close containers
            output_container.close()

            # Write the output to file
            output_buffer.seek(0)
            with open(output_path, "wb") as f:
                f.write(output_buffer.getbuffer())

            results.append(SavedResult(file, subfolder, folder_type))
            counter += 1

        return results