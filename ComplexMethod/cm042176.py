def random_inputs_run_fn(fn, seed, test_val=None, test_buffers=None, expect_match=True):
    input_queues, npy = make_input_queues(vision_input_shapes, policy_input_shapes, frame_skip)
    np.random.seed(seed)
    Tensor.manual_seed(seed)

    for i in range(N_RUNS):
      frame = Tensor.randint(yuv_size, low=0, high=256, dtype='uint8').realize()
      big_frame = Tensor.randint(yuv_size, low=0, high=256, dtype='uint8').realize()
      for v in npy.values():
        v[:] = np.random.randn(*v.shape).astype(v.dtype)
      Device.default.synchronize()
      st = time.perf_counter()
      outs = fn(**input_queues, frame=frame, big_frame=big_frame)
      mt = time.perf_counter()
      for o in outs:
        # .realize() not needed once jitted, but needed for unjitted fn
        o.realize()
      Device.default.synchronize()
      et = time.perf_counter()
      print(f"  [{i+1}/{N_RUNS}] enqueue {(mt-st)*1e3:6.2f} ms -- total {(et-st)*1e3:6.2f} ms")

    val = [np.copy(v.numpy()) for v in outs]
    buffers = [np.copy(v.numpy().copy()) for v in input_queues.values()]

    if test_val is not None:
      match = all(np.array_equal(a, b) for a, b in zip(val, test_val, strict=True))
      assert match == expect_match, f"outputs {'differ from' if expect_match else 'match'} baseline (seed={seed})"
    if test_buffers is not None:
      match = all(np.array_equal(a, b) for a, b in zip(buffers, test_buffers, strict=True))
      assert match == expect_match, f"buffers {'differ from' if expect_match else 'match'} baseline (seed={seed})"
    return fn, val, buffers