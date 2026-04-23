def _extract_chapters_helper(self, chapter_list, start_function, title_function, duration, strict=True):
        if not duration:
            return
        chapter_list = [{
            'start_time': start_function(chapter),
            'title': title_function(chapter),
        } for chapter in chapter_list or []]
        if strict:
            warn = self.report_warning
        else:
            warn = self.write_debug
            chapter_list.sort(key=lambda c: c['start_time'] or 0)

        chapters = [{'start_time': 0}]
        for idx, chapter in enumerate(chapter_list):
            if chapter['start_time'] is None:
                warn(f'Incomplete chapter {idx}')
            elif chapters[-1]['start_time'] <= chapter['start_time'] <= duration:
                chapters.append(chapter)
            elif chapter not in chapters:
                issue = (f'{chapter["start_time"]} > {duration}' if chapter['start_time'] > duration
                         else f'{chapter["start_time"]} < {chapters[-1]["start_time"]}')
                warn(f'Invalid start time ({issue}) for chapter "{chapter["title"]}"')
        return chapters[1:]