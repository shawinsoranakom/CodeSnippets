def extract_chapter_information(e):
            chapters = [{
                'title': part.get('name'),
                'start_time': part.get('startOffset'),
                'end_time': part.get('endOffset'),
            } for part in variadic(e.get('hasPart') or []) if part.get('@type') == 'Clip']
            for idx, (last_c, current_c, next_c) in enumerate(zip(
                    [{'end_time': 0}, *chapters], chapters, chapters[1:], strict=False)):
                current_c['end_time'] = current_c['end_time'] or next_c['start_time']
                current_c['start_time'] = current_c['start_time'] or last_c['end_time']
                if None in current_c.values():
                    self.report_warning(f'Chapter {idx} contains broken data. Not extracting chapters')
                    return
            if chapters:
                chapters[-1]['end_time'] = chapters[-1]['end_time'] or info['duration']
                info['chapters'] = chapters