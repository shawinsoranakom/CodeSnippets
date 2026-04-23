def checkScript(self,
                    script,
                    inputs,
                    name='func',
                    optimize=True,
                    inputs_requires_grad=False,
                    capture_output=False,
                    frames_up=1,
                    profiling=ProfilingMode.PROFILING,
                    atol=None,
                    rtol=None):
        """
        Checks that a given script generates the same output as the Python
        version using the given inputs.
        """
        with torch.jit.optimized_execution(optimize), enable_profiling_mode_for_profiling_tests():
            extra_profile_runs = any(isinstance(x, torch.Tensor) and x.requires_grad for x in inputs)
            if isinstance(script, str):
                # Compile the string to a Script function
                # with enable_profiling_mode():
                cu = torch.jit.CompilationUnit(script, _frames_up=frames_up)

                # Execute the Python function so we can run it later and get its
                # outputs

                frame = self.get_frame_vars(frames_up)
                the_locals: dict[str, Any] = {}
                execWrapper(script, glob=frame, loc=the_locals)
                frame.update(the_locals)

                python_fn = frame[name]
                scripted_fn = getattr(cu, name)
            else:

                # Check the string frontend first
                source = textwrap.dedent(inspect.getsource(script))
                self.checkScript(
                    source,
                    inputs,
                    script.__name__,
                    optimize=optimize,
                    inputs_requires_grad=inputs_requires_grad,
                    capture_output=capture_output,
                    profiling=profiling,
                    frames_up=2)

                # Continue checking the Python frontend
                scripted_fn = torch.jit.script(script, _frames_up=1)
                python_fn = script

            if inputs_requires_grad:
                recording_inputs = do_input_map(lambda t: t.detach().requires_grad_(), inputs)
            else:
                recording_inputs = inputs

            if capture_output:
                with self.capture_stdout() as script_stdout:
                    script_outputs = scripted_fn(*recording_inputs)
                with self.capture_stdout():
                    opt_script_outputs = scripted_fn(*recording_inputs)
                with self.capture_stdout():
                    python_outputs = python_fn(*inputs)
                if not IS_WINDOWS:
                    self.assertExpected(script_stdout[0], subname='stdout')
                self.assertEqual(python_outputs, opt_script_outputs, atol=atol, rtol=rtol)
            else:
                # profiling run
                script_outputs = scripted_fn(*recording_inputs)
                if inputs_requires_grad or extra_profile_runs:
                    opt_script_outputs = scripted_fn(*recording_inputs)
                # optimized run
                opt_script_outputs = scripted_fn(*recording_inputs)
                if TEST_BAILOUTS:
                    self.checkBailouts(scripted_fn, inputs, opt_script_outputs)
                python_outputs = python_fn(*inputs)
            self.assertEqual(python_outputs, script_outputs, atol=atol, rtol=rtol)
            self.assertEqual(script_outputs, opt_script_outputs, atol=atol, rtol=rtol)
            return scripted_fn