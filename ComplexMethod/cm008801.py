def download_and_append_fragments_multiple(self, *args, **kwargs):
        """
        @params (ctx1, fragments1, info_dict1), (ctx2, fragments2, info_dict2), ...
                all args must be either tuple or list
        """
        interrupt_trigger = [True]
        max_progress = len(args)
        if max_progress == 1:
            return self.download_and_append_fragments(*args[0], **kwargs)
        max_workers = self.params.get('concurrent_fragment_downloads', 1)
        if max_progress > 1:
            self._prepare_multiline_status(max_progress)
        is_live = any(traverse_obj(args, (..., 2, 'is_live')))

        def thread_func(idx, ctx, fragments, info_dict, tpe):
            ctx['max_progress'] = max_progress
            ctx['progress_idx'] = idx
            return self.download_and_append_fragments(
                ctx, fragments, info_dict, **kwargs, tpe=tpe, interrupt_trigger=interrupt_trigger)

        class FTPE(concurrent.futures.ThreadPoolExecutor):
            # has to stop this or it's going to wait on the worker thread itself
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        if os.name == 'nt':
            def future_result(future):
                while True:
                    try:
                        return future.result(0.1)
                    except KeyboardInterrupt:
                        raise
                    except concurrent.futures.TimeoutError:
                        continue
        else:
            def future_result(future):
                return future.result()

        def interrupt_trigger_iter(fg):
            for f in fg:
                if not interrupt_trigger[0]:
                    break
                yield f

        spins = []
        for idx, (ctx, fragments, info_dict) in enumerate(args):
            tpe = FTPE(math.ceil(max_workers / max_progress))
            job = tpe.submit(thread_func, idx, ctx, interrupt_trigger_iter(fragments), info_dict, tpe)
            spins.append((tpe, job))

        result = True
        for tpe, job in spins:
            try:
                result = result and future_result(job)
            except KeyboardInterrupt:
                interrupt_trigger[0] = False
            finally:
                tpe.shutdown(wait=True)
        if not interrupt_trigger[0] and not is_live:
            raise KeyboardInterrupt
        # we expect the user wants to stop and DO WANT the preceding postprocessors to run;
        # so returning a intermediate result here instead of KeyboardInterrupt on live
        return result