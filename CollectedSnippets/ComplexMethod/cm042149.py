def _pieces(self, text: str, glossary_href: str) -> list[str | ET.Element]:
    if not text.strip():
      return []

    pieces: list[str | ET.Element] = []
    cursor = 0

    while True:
      best = None
      for slug, pattern, tooltip in self.glossary:
        if slug in self.seen:
          continue

        found = pattern.search(text, cursor)
        if found is None:
          continue

        candidate = (slug, tooltip, found.start(), found.end())
        if best is None:
          best = candidate
          continue

        _, _, best_start, best_end = best
        _, _, current_start, current_end = candidate
        if current_start < best_start:
          best = candidate
          continue

        if current_start == best_start and current_end - current_start > best_end - best_start:
          best = candidate

      if best is None:
        break

      slug, tooltip, start, end = best
      if start > cursor:
        pieces.append(text[cursor:start])

      link = ET.Element(
        "a",
        {
          "class": "glossary-term",
          "data-glossary-term": "",
          "href": f"{glossary_href}{slug}",
        },
      )
      ET.SubElement(link, "span", {"class": "glossary-term__label"}).text = text[start:end]
      ET.SubElement(
        link,
        "span",
        {
          "class": "glossary-term__tooltip",
          "data-search-exclude": "",
        },
      ).text = tooltip
      pieces.append(link)
      self.seen.add(slug)
      cursor = end

    if not pieces:
      return []
    if cursor < len(text):
      pieces.append(text[cursor:])
    return pieces