def _generate_index_html(self, index_path: Path, file_stats: List[FileStats]):
        """Generate index.html with list of all profiled files."""
        # Build hierarchical tree
        tree = _TreeBuilder.build_file_tree(file_stats)

        # Render tree as HTML
        renderer = _HtmlRenderer(self.file_index)
        sections_html = renderer.render_hierarchical_html(tree)

        # Format error rate and missed samples with bar classes
        error_rate = self.stats.get('error_rate')
        if error_rate is not None:
            error_rate_str = f"{fmt(error_rate)}%"
            error_rate_width = min(error_rate, 100)
            # Determine bar color class based on rate
            if error_rate < 5:
                error_rate_class = "good"
            elif error_rate < 15:
                error_rate_class = "warning"
            else:
                error_rate_class = "error"
        else:
            error_rate_str = "N/A"
            error_rate_width = 0
            error_rate_class = "good"

        missed_samples = self.stats.get('missed_samples')
        if missed_samples is not None:
            missed_samples_str = f"{fmt(missed_samples)}%"
            missed_samples_width = min(missed_samples, 100)
            if missed_samples < 5:
                missed_samples_class = "good"
            elif missed_samples < 15:
                missed_samples_class = "warning"
            else:
                missed_samples_class = "error"
        else:
            missed_samples_str = "N/A"
            missed_samples_width = 0
            missed_samples_class = "good"

        # Populate template
        replacements = {
            "<!-- INLINE_CSS -->": f"<style>\n{self._template_loader.index_css}\n</style>",
            "<!-- INLINE_JS -->": f"<script>\n{self._template_loader.index_js}\n</script>",
            "<!-- PYTHON_LOGO -->": self._template_loader.logo_html,
            "<!-- PYTHON_VERSION -->": f"{sys.version_info.major}.{sys.version_info.minor}",
            "<!-- NUM_FILES -->": f"{len(file_stats):n}",
            "<!-- TOTAL_SAMPLES -->": f"{self._total_samples:n}",
            "<!-- DURATION -->": fmt(self.stats.get('duration_sec', 0)),
            "<!-- SAMPLE_RATE -->": fmt(self.stats.get('sample_rate', 0)),
            "<!-- ERROR_RATE -->": error_rate_str,
            "<!-- ERROR_RATE_WIDTH -->": str(error_rate_width),
            "<!-- ERROR_RATE_CLASS -->": error_rate_class,
            "<!-- MISSED_SAMPLES -->": missed_samples_str,
            "<!-- MISSED_SAMPLES_WIDTH -->": str(missed_samples_width),
            "<!-- MISSED_SAMPLES_CLASS -->": missed_samples_class,
            "<!-- SECTIONS_HTML -->": sections_html,
        }

        html_content = self._template_loader.index_template
        for placeholder, value in replacements.items():
            html_content = html_content.replace(placeholder, value)

        try:
            index_path.write_text(html_content, encoding='utf-8')
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to write index file {index_path}: {e}") from e