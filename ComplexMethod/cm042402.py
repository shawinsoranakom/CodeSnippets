def parse_html_content(self, html_content: str) -> None:
    self.elements.clear()
    self._cached_height = None
    self._cached_width = -1

    # Remove HTML comments
    html_content = COMMENT_RE.sub('', html_content)

    # Remove DOCTYPE, html, head, body tags but keep their content
    html_content = DOCTYPE_RE.sub('', html_content)
    html_content = HTML_BODY_TAGS_RE.sub('', html_content)

    # Parse HTML
    tokens = TOKEN_RE.findall(html_content)

    def close_tag():
      nonlocal current_content
      nonlocal current_tag

      # If no tag is set, default to paragraph so we don't lose text
      if current_tag is None:
        current_tag = ElementType.P

      text = ' '.join(current_content).strip()
      current_content = []
      if text:
        if current_tag == ElementType.LI:
          text = '• ' + text
        self._add_element(current_tag, text)

    current_content: list[str] = []
    current_tag: ElementType | None = None
    for token in tokens:
      is_start_tag, is_end_tag, tag = is_tag(token)
      if tag is not None:
        if tag == ElementType.BR:
          # Close current tag and add a line break
          close_tag()
          self._add_element(ElementType.BR, "")

        elif is_start_tag or is_end_tag:
          # Always add content regardless of opening or closing tag
          close_tag()

          if is_start_tag:
            current_tag = tag
          else:
            current_tag = None

        # increment after we add the content for the current tag
        if tag == ElementType.UL:
          self._indent_level = self._indent_level + 1 if is_start_tag else max(0, self._indent_level - 1)

      else:
        current_content.append(token)

    if current_content:
      close_tag()