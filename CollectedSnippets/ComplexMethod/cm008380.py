def _resolve_nuxt_array(self, array, video_id, *, fatal=True, default=NO_DEFAULT):
        """Resolves Nuxt rich JSON payload arrays"""
        # Ref: https://github.com/nuxt/nuxt/commit/9e503be0f2a24f4df72a3ccab2db4d3e63511f57
        #      https://github.com/nuxt/nuxt/pull/19205
        if default is not NO_DEFAULT:
            fatal = False

        if not isinstance(array, list) or not array:
            error_msg = 'Unable to resolve Nuxt JSON data: invalid input'
            if fatal:
                raise ExtractorError(error_msg, video_id=video_id)
            elif default is NO_DEFAULT:
                self.report_warning(error_msg, video_id=video_id)
            return {} if default is NO_DEFAULT else default

        def indirect_reviver(data):
            return data

        def json_reviver(data):
            return json.loads(data)

        gen = devalue.parse_iter(array, revivers={
            'NuxtError': indirect_reviver,
            'EmptyShallowRef': json_reviver,
            'EmptyRef': json_reviver,
            'ShallowRef': indirect_reviver,
            'ShallowReactive': indirect_reviver,
            'Ref': indirect_reviver,
            'Reactive': indirect_reviver,
            'skipHydrate': indirect_reviver,
        })

        while True:
            try:
                error_msg = f'Error resolving Nuxt JSON: {gen.send(None)}'
                if fatal:
                    raise ExtractorError(error_msg, video_id=video_id)
                elif default is NO_DEFAULT:
                    self.report_warning(error_msg, video_id=video_id, only_once=True)
                else:
                    self.write_debug(f'{video_id}: {error_msg}', only_once=True)
            except StopIteration as error:
                return error.value or ({} if default is NO_DEFAULT else default)