def _build_paragraph_style_profile(self, shape, paragraph) -> dict[str, Optional[float] | bool]:
        paragraph_font_sources = self._get_paragraph_font_sources(shape, paragraph)
        effective_font_size_pt = None
        all_bold = True
        has_non_whitespace_run = False

        for run in paragraph.runs:
            run_text = getattr(run, "text", None)
            if run_text is None or not run_text.strip():
                continue

            has_non_whitespace_run = True

            run_font_size_pt = self._resolve_effective_run_font_size_pt(
                run,
                paragraph_font_sources,
            )
            if run_font_size_pt is not None:
                if effective_font_size_pt is None:
                    effective_font_size_pt = run_font_size_pt
                else:
                    effective_font_size_pt = max(
                        effective_font_size_pt,
                        run_font_size_pt,
                    )

            if (
                self._resolve_effective_run_bold(run, paragraph_font_sources)
                is not True
            ):
                all_bold = False

        return {
            "font_size_pt": effective_font_size_pt,
            "all_bold": has_non_whitespace_run and all_bold,
        }