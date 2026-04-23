def extract_thread(contents, entity_payloads, thread_parent, thread_depth):
            if not thread_parent:
                tracker['current_page_thread'] = 0

            if max_depth < thread_depth:
                return

            for content in contents:
                if not thread_parent and tracker['total_parent_comments'] >= max_parents:
                    yield
                comment_thread_renderer = try_get(content, lambda x: x['commentThreadRenderer'])

                # old comment format
                if not entity_payloads:
                    comment_renderer = get_first(
                        (comment_thread_renderer, content), [['commentRenderer', ('comment', 'commentRenderer')]],
                        expected_type=dict, default={})

                    comment = self._extract_comment_old(comment_renderer, thread_parent)

                # new comment format
                else:
                    view_model = (
                        traverse_obj(comment_thread_renderer, ('commentViewModel', 'commentViewModel', {dict}))
                        or traverse_obj(content, ('commentViewModel', {dict})))
                    comment_keys = traverse_obj(view_model, (('commentKey', 'toolbarStateKey'), {str}))
                    if not comment_keys:
                        continue
                    entities = traverse_obj(entity_payloads, lambda _, v: v['entityKey'] in comment_keys)
                    comment = self._extract_comment(entities, thread_parent)
                    if comment:
                        comment['is_pinned'] = traverse_obj(view_model, ('pinnedText', {str})) is not None

                if not comment:
                    continue
                comment_id = comment['id']

                if comment.get('is_pinned'):
                    tracker['pinned_comment_ids'].add(comment_id)
                # Sometimes YouTube may break and give us infinite looping comments.
                # See: https://github.com/yt-dlp/yt-dlp/issues/6290
                if comment_id in tracker['seen_comment_ids']:
                    if comment_id in tracker['pinned_comment_ids'] and not comment.get('is_pinned'):
                        # Pinned comments may appear a second time in newest first sort
                        # See: https://github.com/yt-dlp/yt-dlp/issues/6712
                        continue
                    self.report_warning(
                        'Detected YouTube comments looping. Stopping comment extraction '
                        f'{"for this thread" if thread_parent else ""} as we probably cannot get any more.')
                    yield
                    break  # Safeguard for recursive call in subthreads code path below
                else:
                    tracker['seen_comment_ids'].add(comment_id)

                tracker['running_total'] += 1
                tracker['total_reply_comments' if thread_parent else 'total_parent_comments'] += 1
                yield comment

                # Attempt to get the replies
                comment_replies_renderer = try_get(
                    comment_thread_renderer, lambda x: x['replies']['commentRepliesRenderer'], dict)

                if comment_replies_renderer:
                    subthreads = traverse_obj(comment_replies_renderer, ('subThreads', ..., {dict}))
                    # Recursively extract from `commentThreadRenderer`s in `subThreads`
                    if threads := traverse_obj(subthreads, lambda _, v: v['commentThreadRenderer']):
                        for entry in extract_thread(threads, entity_payloads, comment_id, thread_depth + 1):
                            if entry:
                                yield entry
                        if not traverse_obj(subthreads, lambda _, v: v['continuationItemRenderer']):
                            # All of the subThreads' `continuationItemRenderer`s were within the nested
                            # `commentThreadRenderer`s and are now exhausted, so avoid unnecessary recursion below
                            continue

                    tracker['current_page_thread'] += 1
                    # Recursively extract from `continuationItemRenderer` in `subThreads`
                    comment_entries_iter = self._comment_entries(
                        comment_replies_renderer, ytcfg, video_id,
                        parent=comment_id, tracker=tracker, depth=thread_depth + 1)
                    yield from itertools.islice(comment_entries_iter, min(
                        max_replies_per_thread, max(0, max_replies - tracker['total_reply_comments'])))