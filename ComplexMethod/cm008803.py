def frag_progress_hook(s):
            if s['status'] not in ('downloading', 'finished'):
                return

            if not total_frags and ctx.get('fragment_count'):
                state['fragment_count'] = ctx['fragment_count']

            if ctx_id is not None and s.get('ctx_id') != ctx_id:
                return

            state['max_progress'] = ctx.get('max_progress')
            state['progress_idx'] = ctx.get('progress_idx')

            state['elapsed'] = progress.elapsed
            frag_total_bytes = s.get('total_bytes') or 0
            s['fragment_info_dict'] = s.pop('info_dict', {})

            # XXX: Fragment resume is not accounted for here
            if not ctx['live']:
                estimated_size = (
                    (ctx['complete_frags_downloaded_bytes'] + frag_total_bytes)
                    / (state['fragment_index'] + 1) * total_frags)
                progress.total = estimated_size
                progress.update(s.get('downloaded_bytes'))
                state['total_bytes_estimate'] = progress.total
            else:
                progress.update(s.get('downloaded_bytes'))

            if s['status'] == 'finished':
                state['fragment_index'] += 1
                ctx['fragment_index'] = state['fragment_index']
                progress.thread_reset()

            state['downloaded_bytes'] = ctx['complete_frags_downloaded_bytes'] = progress.downloaded
            state['speed'] = ctx['speed'] = progress.speed.smooth
            state['eta'] = progress.eta.smooth

            self._hook_progress(state, info_dict)