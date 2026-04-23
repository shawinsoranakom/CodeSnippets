def pack_fragment(frag_content, frag_index):
                output = io.StringIO()
                adjust = 0
                overflow = False
                mpegts_last = None
                for block in webvtt.parse_fragment(frag_content):
                    if isinstance(block, webvtt.CueBlock):
                        extra_state['webvtt_mpegts_last'] = mpegts_last
                        if overflow:
                            extra_state['webvtt_mpegts_adjust'] += 1
                            overflow = False
                        block.start += adjust
                        block.end += adjust

                        dedup_window = extra_state.setdefault('webvtt_dedup_window', [])

                        ready = []

                        i = 0
                        is_new = True
                        while i < len(dedup_window):
                            wcue = dedup_window[i]
                            wblock = webvtt.CueBlock.from_json(wcue)
                            i += 1
                            if wblock.hinges(block):
                                wcue['end'] = block.end
                                is_new = False
                                continue
                            if wblock == block:
                                is_new = False
                                continue
                            if wblock.end > block.start:
                                continue
                            ready.append(wblock)
                            i -= 1
                            del dedup_window[i]

                        if is_new:
                            dedup_window.append(block.as_json)
                        for block in ready:
                            block.write_into(output)

                        # we only emit cues once they fall out of the duplicate window
                        continue
                    elif isinstance(block, webvtt.Magic):
                        # take care of MPEG PES timestamp overflow
                        if block.mpegts is None:
                            block.mpegts = 0
                        extra_state.setdefault('webvtt_mpegts_adjust', 0)
                        block.mpegts += extra_state['webvtt_mpegts_adjust'] << 33
                        if block.mpegts < extra_state.get('webvtt_mpegts_last', 0):
                            overflow = True
                            block.mpegts += 1 << 33
                        mpegts_last = block.mpegts

                        if frag_index == 1:
                            extra_state['webvtt_mpegts'] = block.mpegts or 0
                            extra_state['webvtt_local'] = block.local or 0
                            # XXX: block.local = block.mpegts = None ?
                        else:
                            if block.mpegts is not None and block.local is not None:
                                adjust = (
                                    (block.mpegts - extra_state.get('webvtt_mpegts', 0))
                                    - (block.local - extra_state.get('webvtt_local', 0))
                                )
                            continue
                    elif isinstance(block, webvtt.HeaderBlock):
                        if frag_index != 1:
                            # XXX: this should probably be silent as well
                            # or verify that all segments contain the same data
                            self.report_warning(bug_reports_message(
                                f'Discarding a {type(block).__name__} block found in the middle of the stream; '
                                'if the subtitles display incorrectly,'))
                            continue
                    block.write_into(output)

                return output.getvalue().encode()