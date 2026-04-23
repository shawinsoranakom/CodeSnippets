def frag_progress_hook(s):
            if s['status'] not in ('downloading', 'finished'):
                return

            if not total_frags and ctx.get('fragment_count'):
                state['fragment_count'] = ctx['fragment_count']

            time_now = time.time()
            state['elapsed'] = time_now - start
            frag_total_bytes = s.get('total_bytes') or 0
            if not ctx['live']:
                estimated_size = (
                    (ctx['complete_frags_downloaded_bytes'] + frag_total_bytes)
                    / (state['fragment_index'] + 1) * total_frags)
                state['total_bytes_estimate'] = estimated_size

            if s['status'] == 'finished':
                state['fragment_index'] += 1
                ctx['fragment_index'] = state['fragment_index']
                state['downloaded_bytes'] += frag_total_bytes - ctx['prev_frag_downloaded_bytes']
                ctx['complete_frags_downloaded_bytes'] = state['downloaded_bytes']
                ctx['speed'] = state['speed'] = self.calc_speed(
                    ctx['fragment_started'], time_now, frag_total_bytes)
                ctx['fragment_started'] = time.time()
                ctx['prev_frag_downloaded_bytes'] = 0
            else:
                frag_downloaded_bytes = s['downloaded_bytes']
                state['downloaded_bytes'] += frag_downloaded_bytes - ctx['prev_frag_downloaded_bytes']
                ctx['speed'] = state['speed'] = self.calc_speed(
                    ctx['fragment_started'], time_now, frag_downloaded_bytes - ctx['frag_resume_len'])
                if not ctx['live']:
                    state['eta'] = self.calc_eta(state['speed'], estimated_size - state['downloaded_bytes'])
                ctx['prev_frag_downloaded_bytes'] = frag_downloaded_bytes
            self._hook_progress(state)