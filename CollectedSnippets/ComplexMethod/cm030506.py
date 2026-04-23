def _build_line_html(self, line_num: int, line_content: str,
                        line_counts: Dict[int, int], self_counts: Dict[int, int],
                        max_samples: int, max_self_samples: int, filename: str) -> str:
        """Build HTML for a single line of source code."""
        cumulative_samples = line_counts.get(line_num, 0)
        self_samples = self_counts.get(line_num, 0)

        # Calculate colors for both self and cumulative modes
        if cumulative_samples > 0:
            log_cumulative = math.log(cumulative_samples + 1)
            log_max = math.log(max_samples + 1)
            cumulative_intensity = log_cumulative / log_max if log_max > 0 else 0

            if self_samples > 0 and max_self_samples > 0:
                log_self = math.log(self_samples + 1)
                log_max_self = math.log(max_self_samples + 1)
                self_intensity = log_self / log_max_self if log_max_self > 0 else 0
            else:
                self_intensity = 0

            self_display = f"{self_samples:n}" if self_samples > 0 else ""
            cumulative_display = f"{cumulative_samples:n}"
            tooltip = f"Self: {self_samples:n}, Total: {cumulative_samples:n}"
        else:
            cumulative_intensity = 0
            self_intensity = 0
            self_display = ""
            cumulative_display = ""
            tooltip = ""

        # Get bytecode data for this line (if any)
        bytecode_data = self._get_bytecode_data_for_line(filename, line_num)
        has_bytecode = len(bytecode_data) > 0 and cumulative_samples > 0

        # Build bytecode toggle button if data is available
        bytecode_btn_html = ''
        bytecode_panel_html = ''
        if has_bytecode:
            bytecode_json = html.escape(json.dumps(bytecode_data))

            # Calculate specialization percentage
            total_samples = sum(d['samples'] for d in bytecode_data)
            specialized_samples = sum(d['samples'] for d in bytecode_data if d['is_specialized'])
            spec_pct = int(100 * specialized_samples / total_samples) if total_samples > 0 else 0

            bytecode_btn_html = (
                f'<button class="bytecode-toggle" data-bytecode=\'{bytecode_json}\' '
                f'data-spec-pct="{spec_pct}" '
                f'onclick="toggleBytecode(this)" title="Show bytecode">&#9654;</button>'
            )
            # Wrapper contains columns + content panel
            bytecode_panel_html = (
                f'        <div class="bytecode-wrapper" id="bytecode-wrapper-{line_num}">\n'
                f'            <div class="bytecode-columns">'
                f'<div class="line-number"></div>'
                f'<div class="line-samples-self"></div>'
                f'<div class="line-samples-cumulative"></div>'
                f'</div>\n'
                f'            <div class="bytecode-panel" id="bytecode-{line_num}"></div>\n'
                f'        </div>\n'
            )
        elif self.opcodes_enabled:
            # Add invisible spacer to maintain consistent indentation when opcodes are enabled
            bytecode_btn_html = '<div class="bytecode-spacer"></div>'

        # Get navigation buttons
        nav_buttons_html = self._build_navigation_buttons(filename, line_num)

        # Build line HTML with instruction highlights if available
        line_html = self._render_source_with_highlights(line_content, line_num,
                                                         filename, bytecode_data)
        title_attr = f' title="{html.escape(tooltip)}"' if tooltip else ""

        # Specialization color for toggle mode (green gradient based on spec %)
        spec_color_attr = ''
        if has_bytecode:
            spec_color = self._format_specialization_color(spec_pct)
            spec_color_attr = f'data-spec-color="{spec_color}" '

        return (
            f'        <div class="code-line" '
            f'data-self-intensity="{self_intensity:.3f}" '
            f'data-cumulative-intensity="{cumulative_intensity:.3f}" '
            f'{spec_color_attr}'
            f'id="line-{line_num}"{title_attr}>\n'
            f'            <div class="line-number">{line_num}</div>\n'
            f'            <div class="line-samples-self">{self_display}</div>\n'
            f'            <div class="line-samples-cumulative">{cumulative_display}</div>\n'
            f'            {bytecode_btn_html}\n'
            f'            <div class="line-content">{line_html}</div>\n'
            f'            {nav_buttons_html}\n'
            f'        </div>\n'
            f'{bytecode_panel_html}'
        )