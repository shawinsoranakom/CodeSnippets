def _build_paragraph_rich_text(self, paragraph, shape) -> str:
        """按 run 维度构建段落富文本，支持样式与超链接标签。"""
        paragraph_font_sources = self._get_paragraph_font_sources(shape, paragraph)
        run_map = {}
        for run in paragraph.runs:
            try:
                run_map[id(run._r)] = run
            except Exception:
                continue

        segments = []

        for node in paragraph._element.content_children:
            if isinstance(node, CT_TextLineBreak):
                segments.append(
                    {
                        "text": " ",
                        "style_str": None,
                        "hyperlink": None,
                    }
                )
                continue

            if self._is_math_content_node(node):
                latex = self._convert_math_node_to_latex(node)
                if latex:
                    segments.append(
                        {
                            "text": self.equation_bookends.format(EQ=latex),
                            "style_str": None,
                            "hyperlink": None,
                        }
                    )
                    continue

            node_text = getattr(node, "text", None)
            if node_text is None:
                continue
            if node_text == "":
                continue

            run = run_map.get(id(node))
            if run is None:
                segments.append(
                    {
                        "text": node_text,
                        "style_str": None,
                        "hyperlink": None,
                    }
                )
                continue

            segments.append(
                {
                    "text": node_text,
                    "style_str": self._get_style_str_from_run(
                        run,
                        paragraph_font_sources,
                    ),
                    "hyperlink": self._resolve_hyperlink_from_run(run, shape),
                }
            )

        segments = self._trim_rich_text_segments(segments)
        if not segments:
            return ""

        merged_segments = []
        for segment in segments:
            if (
                merged_segments
                and merged_segments[-1]["hyperlink"] is None
                and segment["hyperlink"] is None
                and merged_segments[-1]["style_str"] == segment["style_str"]
            ):
                merged_segments[-1]["text"] += segment["text"]
            else:
                merged_segments.append(segment)

        return "".join(
            self._format_text_with_hyperlink(
                segment["text"],
                segment["hyperlink"],
                segment["style_str"],
            )
            for segment in merged_segments
        )