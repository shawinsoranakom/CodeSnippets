def iterate_subtitles():
            line_len = 0
            line_count = 1
            # the next subtitle to yield (a list of word timings with whitespace)
            subtitle: List[dict] = []
            last: float = get_start(result["segments"]) or 0.0
            for segment in result["segments"]:
                chunk_index = 0
                words_count = max_words_per_line
                while chunk_index < len(segment["words"]):
                    remaining_words = len(segment["words"]) - chunk_index
                    if max_words_per_line > len(segment["words"]) - chunk_index:
                        words_count = remaining_words
                    for i, original_timing in enumerate(
                        segment["words"][chunk_index : chunk_index + words_count]
                    ):
                        timing = original_timing.copy()
                        long_pause = (
                            not preserve_segments and timing["start"] - last > 3.0
                        )
                        has_room = line_len + len(timing["word"]) <= max_line_width
                        seg_break = i == 0 and len(subtitle) > 0 and preserve_segments
                        if (
                            line_len > 0
                            and has_room
                            and not long_pause
                            and not seg_break
                        ):
                            # line continuation
                            line_len += len(timing["word"])
                        else:
                            # new line
                            timing["word"] = timing["word"].strip()
                            if (
                                len(subtitle) > 0
                                and max_line_count is not None
                                and (long_pause or line_count >= max_line_count)
                                or seg_break
                            ):
                                # subtitle break
                                yield subtitle
                                subtitle = []
                                line_count = 1
                            elif line_len > 0:
                                # line break
                                line_count += 1
                                timing["word"] = "\n" + timing["word"]
                            line_len = len(timing["word"].strip())
                        subtitle.append(timing)
                        last = timing["start"]
                    chunk_index += max_words_per_line
            if len(subtitle) > 0:
                yield subtitle