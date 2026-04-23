def _remove_tiny_rename_sponsors(self, chapters):
        new_chapters = []
        for i, c in enumerate(chapters):
            # Merge with the previous/next if the chapter is tiny.
            # Only tiny chapters resulting from a cut can be skipped.
            # Chapters that were already tiny in the original list will be preserved.
            if (('_was_cut' in c or '_categories' in c)
                    and c['end_time'] - c['start_time'] < _TINY_CHAPTER_DURATION):
                if not new_chapters:
                    # Prepend tiny chapter to the next one if possible.
                    if i < len(chapters) - 1:
                        chapters[i + 1]['start_time'] = c['start_time']
                        continue
                else:
                    old_c = new_chapters[-1]
                    if i < len(chapters) - 1:
                        next_c = chapters[i + 1]
                        # Not a typo: key names in old_c and next_c are really different.
                        prev_is_sponsor = 'categories' in old_c
                        next_is_sponsor = '_categories' in next_c
                        # Preferentially prepend tiny normals to normals and sponsors to sponsors.
                        if (('_categories' not in c and prev_is_sponsor and not next_is_sponsor)
                                or ('_categories' in c and not prev_is_sponsor and next_is_sponsor)):
                            next_c['start_time'] = c['start_time']
                            continue
                    old_c['end_time'] = c['end_time']
                    continue

            c.pop('_was_cut', None)
            cats = c.pop('_categories', None)
            if cats:
                category, _, _, category_name = min(cats, key=lambda c: c[2] - c[1])
                c.update({
                    'category': category,
                    'categories': orderedSet(x[0] for x in cats),
                    'name': category_name,
                    'category_names': orderedSet(x[3] for x in cats),
                })
                c['title'] = self._downloader.evaluate_outtmpl(self._sponsorblock_chapter_title, c.copy())
                # Merge identically named sponsors.
                if (new_chapters and 'categories' in new_chapters[-1]
                        and new_chapters[-1]['title'] == c['title']):
                    new_chapters[-1]['end_time'] = c['end_time']
                    continue
            new_chapters.append(c)
        return new_chapters