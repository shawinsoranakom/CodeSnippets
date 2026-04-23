def citation_replacer(match: re.Match[str]):
                                                ref_type = match.group(1)
                                                ref_index = int(match.group(2))
                                                if ((ref_type == "image" and is_image_embedding) or
                                                        is_video_embedding or
                                                        ref_type == "forecast"):

                                                    reference = references.get_reference({
                                                        "ref_index": ref_index,
                                                        "ref_type": ref_type
                                                    })
                                                    if not reference:
                                                        return ""

                                                    if ref_type == "forecast":
                                                        if reference.get("alt"):
                                                            return reference.get("alt")
                                                        if reference.get("prompt_text"):
                                                            return reference.get("prompt_text")

                                                    if is_image_embedding and reference.get("content_url", ""):
                                                        return f"![{reference.get('title', '')}]({reference.get('content_url')})"

                                                    if is_video_embedding:
                                                        if reference.get("url", "") and reference.get("thumbnail_url",
                                                                                                      ""):
                                                            return f"[![{reference.get('title', '')}]({reference['thumbnail_url']})]({reference['url']})"
                                                        video_match = re.match(r"video\n(.*?)\nturn[0-9]+",
                                                                               match.group(0))
                                                        if video_match:
                                                            return video_match.group(1)
                                                    return ""

                                                source_index = sources.get_index({
                                                    "ref_index": ref_index,
                                                    "ref_type": ref_type
                                                })
                                                if source_index is not None and len(sources.list) > source_index:
                                                    link = sources.list[source_index]["url"]
                                                    return f"[[{source_index + 1}]]({link})"
                                                return f""