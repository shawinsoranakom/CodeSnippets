def _generate_file_html(self, output_path: Path, filename: str,
                          line_counts: Dict[int, int], self_counts: Dict[int, int],
                          file_stat: FileStats):
        """Generate HTML for a single source file with heatmap coloring."""
        # Read source file
        try:
            source_lines = Path(filename).read_text(encoding='utf-8', errors='replace').splitlines()
        except (IOError, OSError) as e:
            if not (filename.startswith('<') or filename.startswith('[') or
                    filename in ('~', '...', '.') or len(filename) < 2):
                print(f"Warning: Could not read source file {filename}: {e}")
            source_lines = [f"# Source file not available: {filename}"]

        # Generate HTML for each line
        max_samples = max(line_counts.values()) if line_counts else 1
        max_self_samples = max(self_counts.values()) if self_counts else 1
        code_lines_html = [
            self._build_line_html(line_num, line_content, line_counts, self_counts,
                                max_samples, max_self_samples, filename)
            for line_num, line_content in enumerate(source_lines, start=1)
        ]

        # Populate template
        replacements = {
            "<!-- FILENAME -->": html.escape(filename),
            "<!-- TOTAL_SAMPLES -->": f"{file_stat.total_samples:n}",
            "<!-- TOTAL_SELF_SAMPLES -->": f"{file_stat.total_self_samples:n}",
            "<!-- NUM_LINES -->": f"{file_stat.num_lines:n}",
            "<!-- PERCENTAGE -->": fmt(file_stat.percentage, 2),
            "<!-- MAX_SAMPLES -->": f"{file_stat.max_samples:n}",
            "<!-- MAX_SELF_SAMPLES -->": f"{file_stat.max_self_samples:n}",
            "<!-- CODE_LINES -->": ''.join(code_lines_html),
            "<!-- INLINE_CSS -->": f"<style>\n{self._template_loader.file_css}\n</style>",
            "<!-- INLINE_JS -->": f"<script>\n{self._template_loader.file_js}\n</script>",
            "<!-- PYTHON_LOGO -->": self._template_loader.logo_html,
            "<!-- PYTHON_VERSION -->": f"{sys.version_info.major}.{sys.version_info.minor}",
        }

        html_content = self._template_loader.file_template
        for placeholder, value in replacements.items():
            html_content = html_content.replace(placeholder, value)

        try:
            output_path.write_text(html_content, encoding='utf-8')
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to write file {output_path}: {e}") from e