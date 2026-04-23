def _compared_saved_loaded(self, m):
        def extract_files(buffer):
            # crack open the zip format to get at the main module code
            with zipfile.ZipFile(buffer) as archive:
                # check that we have no duplicate names
                self.assertEqual(len(set(archive.namelist())), len(archive.namelist()))
                files = list(filter(lambda x: x.startswith('archive/code/'), archive.namelist()))
                # unwrap all the code files into strings
                code_files_str = filter(lambda x: x.endswith('.py'), files)
                code_files = []
                for f in code_files_str:
                    with archive.open(f) as stream:
                        code_files.append("".join([line.decode() for line in stream]))

                # unpickled all the debug files
                debug_files_str = filter(lambda f: f.endswith('.debug_pkl'), files)
                debug_files = []
                for f in debug_files_str:
                    with archive.open(f) as stream:
                        debug_files.append(pickle.load(stream))
                return code_files, debug_files

        # disable the hook while we parse code, otherwise we will re-enter the hook
        with torch._jit_internal._disable_emit_hooks():
            try:
                # short-circuit if this is an empty function or module
                if len(m.code) == 0:
                    return
                if isinstance(m, torch._C.ScriptModule):
                    if len(m._method_names()) == 0:
                        return

                # save the module to a buffer
                buffer = io.BytesIO()
                torch.jit.save(m, buffer)
                # copy the data in the buffer so we can restore it later. This
                # is because py2 and py3 have different semantics with zipfile
                # and it's easier to just work with a fresh copy each time.
                buffer_copy = buffer.getvalue()

                code_files, _debug_files = extract_files(buffer)

            except RuntimeError as e:
                if not self._isHookExceptionOk(e):
                    raise
                else:
                    return

            # import the model again (from a the copy we made of the original)
            buffer2 = io.BytesIO(buffer_copy)
            imported = torch.jit.load(buffer2)

            # save it again
            saved_module_buffer_2 = io.BytesIO()
            torch.jit.save(imported, saved_module_buffer_2)

            saved_module_buffer_2.seek(0)
            code_files_2, _debug_files_2 = extract_files(saved_module_buffer_2)

            for a, b in zip(code_files, code_files_2, strict=True):
                self.assertMultiLineEqual(a, b)

            if isinstance(m, torch._C.ScriptModule):
                self.assertTrue(torch._C._ivalue_tags_match(m, imported._c))