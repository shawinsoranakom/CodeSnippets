def _get_stream_info_guesses(
        self, file_stream: BinaryIO, base_guess: StreamInfo
    ) -> List[StreamInfo]:
        """
        Given a base guess, attempt to guess or expand on the stream info using the stream content (via magika).
        """
        guesses: List[StreamInfo] = []

        # Enhance the base guess with information based on the extension or mimetype
        enhanced_guess = base_guess.copy_and_update()

        # If there's an extension and no mimetype, try to guess the mimetype
        if base_guess.mimetype is None and base_guess.extension is not None:
            _m, _ = mimetypes.guess_type(
                "placeholder" + base_guess.extension, strict=False
            )
            if _m is not None:
                enhanced_guess = enhanced_guess.copy_and_update(mimetype=_m)

        # If there's a mimetype and no extension, try to guess the extension
        if base_guess.mimetype is not None and base_guess.extension is None:
            _e = mimetypes.guess_all_extensions(base_guess.mimetype, strict=False)
            if len(_e) > 0:
                enhanced_guess = enhanced_guess.copy_and_update(extension=_e[0])

        # Call magika to guess from the stream
        cur_pos = file_stream.tell()
        try:
            result = self._magika.identify_stream(file_stream)
            if result.status == "ok" and result.prediction.output.label != "unknown":
                # If it's text, also guess the charset
                charset = None
                if result.prediction.output.is_text:
                    # Read the first 4k to guess the charset
                    file_stream.seek(cur_pos)
                    stream_page = file_stream.read(4096)
                    charset_result = charset_normalizer.from_bytes(stream_page).best()

                    if charset_result is not None:
                        charset = self._normalize_charset(charset_result.encoding)

                # Normalize the first extension listed
                guessed_extension = None
                if len(result.prediction.output.extensions) > 0:
                    guessed_extension = "." + result.prediction.output.extensions[0]

                # Determine if the guess is compatible with the base guess
                compatible = True
                if (
                    base_guess.mimetype is not None
                    and base_guess.mimetype != result.prediction.output.mime_type
                ):
                    compatible = False

                if (
                    base_guess.extension is not None
                    and base_guess.extension.lstrip(".")
                    not in result.prediction.output.extensions
                ):
                    compatible = False

                if (
                    base_guess.charset is not None
                    and self._normalize_charset(base_guess.charset) != charset
                ):
                    compatible = False

                if compatible:
                    # Add the compatible base guess
                    guesses.append(
                        StreamInfo(
                            mimetype=base_guess.mimetype
                            or result.prediction.output.mime_type,
                            extension=base_guess.extension or guessed_extension,
                            charset=base_guess.charset or charset,
                            filename=base_guess.filename,
                            local_path=base_guess.local_path,
                            url=base_guess.url,
                        )
                    )
                else:
                    # The magika guess was incompatible with the base guess, so add both guesses
                    guesses.append(enhanced_guess)
                    guesses.append(
                        StreamInfo(
                            mimetype=result.prediction.output.mime_type,
                            extension=guessed_extension,
                            charset=charset,
                            filename=base_guess.filename,
                            local_path=base_guess.local_path,
                            url=base_guess.url,
                        )
                    )
            else:
                # There were no other guesses, so just add the base guess
                guesses.append(enhanced_guess)
        finally:
            file_stream.seek(cur_pos)

        return guesses