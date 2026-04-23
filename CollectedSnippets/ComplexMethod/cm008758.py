def _remove_marked_arrange_sponsors(self, chapters):
        # Store cuts separately, since adjacent and overlapping cuts must be merged.
        cuts = []

        def append_cut(c):
            assert 'remove' in c, 'Not a cut is appended to cuts'
            last_to_cut = cuts[-1] if cuts else None
            if last_to_cut and last_to_cut['end_time'] >= c['start_time']:
                last_to_cut['end_time'] = max(last_to_cut['end_time'], c['end_time'])
            else:
                cuts.append(c)
            return len(cuts) - 1

        def excess_duration(c):
            # Cuts that are completely within the chapter reduce chapters' duration.
            # Since cuts can overlap, excess duration may be less that the sum of cuts' durations.
            # To avoid that, chapter stores the index to the fist cut within the chapter,
            # instead of storing excess duration. append_cut ensures that subsequent cuts (if any)
            # will be merged with previous ones (if necessary).
            cut_idx, excess = c.pop('cut_idx', len(cuts)), 0
            while cut_idx < len(cuts):
                cut = cuts[cut_idx]
                if cut['start_time'] >= c['end_time']:
                    break
                if cut['end_time'] > c['start_time']:
                    excess += min(cut['end_time'], c['end_time'])
                    excess -= max(cut['start_time'], c['start_time'])
                cut_idx += 1
            return excess

        new_chapters = []

        def append_chapter(c):
            assert 'remove' not in c, 'Cut is appended to chapters'
            length = c['end_time'] - c['start_time'] - excess_duration(c)
            # Chapter is completely covered by cuts or sponsors.
            if length <= 0:
                return
            start = new_chapters[-1]['end_time'] if new_chapters else 0
            c.update(start_time=start, end_time=start + length)
            new_chapters.append(c)

        # Turn into a priority queue, index is a tie breaker.
        # Plain stack sorted by start_time is not enough: after splitting the chapter,
        # the part returned to the stack is not guaranteed to have start_time
        # less than or equal to the that of the stack's head.
        chapters = [(c['start_time'], i, c) for i, c in enumerate(chapters)]
        heapq.heapify(chapters)

        _, cur_i, cur_chapter = heapq.heappop(chapters)
        while chapters:
            _, i, c = heapq.heappop(chapters)
            # Non-overlapping chapters or cuts can be appended directly. However,
            # adjacent non-overlapping cuts must be merged, which is handled by append_cut.
            if cur_chapter['end_time'] <= c['start_time']:
                (append_chapter if 'remove' not in cur_chapter else append_cut)(cur_chapter)
                cur_i, cur_chapter = i, c
                continue

            # Eight possibilities for overlapping chapters: (cut, cut), (cut, sponsor),
            # (cut, normal), (sponsor, cut), (normal, cut), (sponsor, sponsor),
            # (sponsor, normal), and (normal, sponsor). There is no (normal, normal):
            # normal chapters are assumed not to overlap.
            if 'remove' in cur_chapter:
                # (cut, cut): adjust end_time.
                if 'remove' in c:
                    cur_chapter['end_time'] = max(cur_chapter['end_time'], c['end_time'])
                # (cut, sponsor/normal): chop the beginning of the later chapter
                # (if it's not completely hidden by the cut). Push to the priority queue
                # to restore sorting by start_time: with beginning chopped, c may actually
                # start later than the remaining chapters from the queue.
                elif cur_chapter['end_time'] < c['end_time']:
                    c['start_time'] = cur_chapter['end_time']
                    c['_was_cut'] = True
                    heapq.heappush(chapters, (c['start_time'], i, c))
            # (sponsor/normal, cut).
            elif 'remove' in c:
                cur_chapter['_was_cut'] = True
                # Chop the end of the current chapter if the cut is not contained within it.
                # Chopping the end doesn't break start_time sorting, no PQ push is necessary.
                if cur_chapter['end_time'] <= c['end_time']:
                    cur_chapter['end_time'] = c['start_time']
                    append_chapter(cur_chapter)
                    cur_i, cur_chapter = i, c
                    continue
                # Current chapter contains the cut within it. If the current chapter is
                # a sponsor chapter, check whether the categories before and after the cut differ.
                if '_categories' in cur_chapter:
                    after_c = dict(cur_chapter, start_time=c['end_time'], _categories=[])
                    cur_cats = []
                    for cat_start_end in cur_chapter['_categories']:
                        if cat_start_end[1] < c['start_time']:
                            cur_cats.append(cat_start_end)
                        if cat_start_end[2] > c['end_time']:
                            after_c['_categories'].append(cat_start_end)
                    cur_chapter['_categories'] = cur_cats
                    if cur_chapter['_categories'] != after_c['_categories']:
                        # Categories before and after the cut differ: push the after part to PQ.
                        heapq.heappush(chapters, (after_c['start_time'], cur_i, after_c))
                        cur_chapter['end_time'] = c['start_time']
                        append_chapter(cur_chapter)
                        cur_i, cur_chapter = i, c
                        continue
                # Either sponsor categories before and after the cut are the same or
                # we're dealing with a normal chapter. Just register an outstanding cut:
                # subsequent append_chapter will reduce the duration.
                cur_chapter.setdefault('cut_idx', append_cut(c))
            # (sponsor, normal): if a normal chapter is not completely overlapped,
            # chop the beginning of it and push it to PQ.
            elif '_categories' in cur_chapter and '_categories' not in c:
                if cur_chapter['end_time'] < c['end_time']:
                    c['start_time'] = cur_chapter['end_time']
                    c['_was_cut'] = True
                    heapq.heappush(chapters, (c['start_time'], i, c))
            # (normal, sponsor) and (sponsor, sponsor)
            else:
                assert '_categories' in c, 'Normal chapters overlap'
                cur_chapter['_was_cut'] = True
                c['_was_cut'] = True
                # Push the part after the sponsor to PQ.
                if cur_chapter['end_time'] > c['end_time']:
                    # deepcopy to make categories in after_c and cur_chapter/c refer to different lists.
                    after_c = dict(copy.deepcopy(cur_chapter), start_time=c['end_time'])
                    heapq.heappush(chapters, (after_c['start_time'], cur_i, after_c))
                # Push the part after the overlap to PQ.
                elif c['end_time'] > cur_chapter['end_time']:
                    after_cur = dict(copy.deepcopy(c), start_time=cur_chapter['end_time'])
                    heapq.heappush(chapters, (after_cur['start_time'], cur_i, after_cur))
                    c['end_time'] = cur_chapter['end_time']
                # (sponsor, sponsor): merge categories in the overlap.
                if '_categories' in cur_chapter:
                    c['_categories'] = cur_chapter['_categories'] + c['_categories']
                # Inherit the cuts that the current chapter has accumulated within it.
                if 'cut_idx' in cur_chapter:
                    c['cut_idx'] = cur_chapter['cut_idx']
                cur_chapter['end_time'] = c['start_time']
                append_chapter(cur_chapter)
                cur_i, cur_chapter = i, c
        (append_chapter if 'remove' not in cur_chapter else append_cut)(cur_chapter)
        return self._remove_tiny_rename_sponsors(new_chapters), cuts