def run(module, op, args, kwargs):
            torch.cuda.manual_seed(5)

            # Each path runs a dummy op to increment the state a bit before creating controls.
            if module == "torch":
                dummy = getattr(torch, op)(*args, **kwargs)
                control1 = getattr(torch, op)(*args, **kwargs)
                control2 = getattr(torch, op)(*args, **kwargs)
            else:
                dummy = alloc.clone()
                control1 = alloc.clone()
                control2 = alloc.clone()
                getattr(dummy, op)(*args)
                getattr(control1, op)(*args)
                getattr(control2, op)(*args)

            stream = torch.cuda.Stream()
            stream.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(stream):
                torch.cuda.manual_seed(5)

                g = torch.cuda.CUDAGraph()
                torch.cuda.empty_cache()
                if module == "torch":
                    g.capture_begin()
                    t1 = getattr(torch, op)(*args, **kwargs)
                    t2 = getattr(torch, op)(*args, **kwargs)
                    g.capture_end()
                else:
                    t1 = alloc.clone()
                    t2 = alloc.clone()
                    g.capture_begin()
                    getattr(t1, op)(*args)
                    getattr(t2, op)(*args)
                    g.capture_end()
            torch.cuda.current_stream().wait_stream(stream)

            if not TEST_CUDAMALLOCASYNC:
                # Makes sure values haven't been populated yet
                # (in other words, makes sure capture didn't actually run ops).
                # We can only try this with the native allocator, for which captured
                # addresses are already backed by cudaMalloced memory.
                # If we try it with cudaMallocAsync, CUDA won't event consider
                # the captured addresses allocated until replay(), and if we
                # access them before replay() we get IMAs.
                try:
                    self.assertNotEqual(control1, t1)
                    self.assertNotEqual(control2, t2)
                except Exception as e:
                    raise RuntimeError("Failed on " + module + "." + op) from e

            # Set a new seed to check if graph would use it
            for seed in [6, 314, 271]:
                torch.cuda.manual_seed(seed)
                # Runs a dummy op prelude, as for controls, to make sure replay()
                # picks up the dummy op's state increment.
                if module == "torch":
                    dummy = getattr(torch, op)(*args, **kwargs)
                    control1 = getattr(torch, op)(*args, **kwargs)
                    control2 = getattr(torch, op)(*args, **kwargs)
                else:
                    getattr(dummy, op)(*args)
                    getattr(control1, op)(*args)
                    getattr(control2, op)(*args)

                torch.cuda.manual_seed(seed)
                if module == "torch":
                    dummy = getattr(torch, op)(*args, **kwargs)
                else:
                    getattr(dummy, op)(*args)

                # see above comment on TEST_CUDAMALLOCASYNC
                if not TEST_CUDAMALLOCASYNC:
                    t1.copy_(alloc)
                    t2.copy_(alloc)

                # Runs RNG ops that fill t1 and t2.
                g.replay()

                try:
                    self.assertEqual(control1, t1)
                    self.assertEqual(control2, t2)
                except Exception as e:
                    raise RuntimeError("Failed on " + module + "." + op) from e

            # We hold references to all tensors used across streams up til this sync,
            # so no need to call record_stream on those tensors.
            torch.cuda.synchronize()