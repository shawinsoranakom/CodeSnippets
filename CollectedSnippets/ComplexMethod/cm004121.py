def extract_speaker_dict(self, text: str | list[str]) -> list[dict] | str | list[list[dict] | str]:
        """
        Extract speaker dictionary from raw output, returning original text on failure.

        Args:
            text (`str` or `list[str]`):
                Single text or batch of texts to parse from the output of `decode` with `return_format="raw"`.

        Returns:
            Parsed output(s). For single input, returns `list[dict]` or `str`.
            For batch input, returns `list[list[dict] | str]`.
        """
        is_single = isinstance(text, str)
        if is_single:
            text = [text]

        speaker_dict = []
        for t in text:
            t = t.strip()
            if t.startswith("assistant"):
                t = t[len("assistant") :].strip()

            if not t.startswith("["):
                logger.warning("Output doesn't start with '[', likely not JSON array.")
                speaker_dict.append(t)
                continue

            segments = json.loads(t)
            if not isinstance(segments, list):
                logger.warning(f"Expected list, got {type(segments).__name__}.")
                speaker_dict.append(t)
                continue

            if segments and not all(isinstance(seg, dict) and "Content" in seg for seg in segments):
                logger.warning("Not all segments have expected structure.")
                speaker_dict.append(t)
                continue

            time_stamps_valid = True
            for seg in segments:
                if isinstance(seg, dict):
                    for key in ("Start", "End"):
                        val = seg.get(key, None)
                        if val is not None and not isinstance(val, float):
                            if isinstance(val, (int, float)):
                                seg[key] = float(val)
                            else:
                                logger.warning(f"Expected '{key}' to be a number, got {type(val).__name__}.")
                                time_stamps_valid = False
                                break
                else:
                    logger.warning(f"Expected segment to be dict, got {type(seg).__name__}.")
                    time_stamps_valid = False
                    break

            if not time_stamps_valid:
                speaker_dict.append(t)
            else:
                speaker_dict.append(segments)

        return speaker_dict[0] if is_single else speaker_dict