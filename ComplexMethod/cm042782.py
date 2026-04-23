def yield_deltas(completion_gen: CompletionGen) -> Iterable[str]:
            full_response: str = ""
            stream = completion_gen.response
            for delta in stream:
                if isinstance(delta, str):
                    full_response += str(delta)
                elif isinstance(delta, ChatResponse):
                    full_response += delta.delta or ""
                yield full_response
                time.sleep(0.02)

            if completion_gen.sources:
                full_response += SOURCES_SEPARATOR
                cur_sources = Source.curate_sources(completion_gen.sources)
                sources_text = "\n\n\n"
                used_files = set()
                for index, source in enumerate(cur_sources, start=1):
                    if f"{source.file}-{source.page}" not in used_files:
                        sources_text = (
                            sources_text
                            + f"{index}. {source.file} (page {source.page}) \n\n"
                        )
                        used_files.add(f"{source.file}-{source.page}")
                sources_text += "<hr>\n\n"
                full_response += sources_text
            yield full_response