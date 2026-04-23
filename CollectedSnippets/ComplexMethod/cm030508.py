def _create_navigation_button(self, items_with_counts: List[Tuple[str, int, str, int]],
                                 btn_class: str, arrow: str) -> str:
        """Create HTML for a navigation button with sample counts."""
        # Filter valid items
        valid_items = [(f, l, fn, cnt) for f, l, fn, cnt in items_with_counts
                      if f in self.file_index and l > 0]
        if not valid_items:
            return ""

        if len(valid_items) == 1:
            file, line, func, count = valid_items[0]
            target_html = self.file_index[file]
            nav_data = json.dumps({'link': f"{target_html}#line-{line}", 'func': func})
            title = f"Go to {btn_class}: {html.escape(func)} ({count:n} samples)"
            return f'<button class="nav-btn {btn_class}" data-nav=\'{html.escape(nav_data)}\' title="{title}">{arrow}</button>'

        # Multiple items - create menu
        total_samples = sum(cnt for _, _, _, cnt in valid_items)
        items_data = [
            {
                'file': os.path.basename(file),
                'func': func,
                'count': count,
                'link': f"{self.file_index[file]}#line-{line}"
            }
            for file, line, func, count in valid_items
        ]
        items_json = html.escape(json.dumps(items_data))
        title = f"{len(items_data)} {btn_class}s ({total_samples:n} samples)"
        return f'<button class="nav-btn {btn_class}" data-nav-multi=\'{items_json}\' title="{title}">{arrow}</button>'