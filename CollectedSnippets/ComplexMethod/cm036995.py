def benchmark():
    from triton.testing import do_bench

    # similar to llama 3.1-8B
    llama_config = LlamaConfig(
        hidden_size=4096, mlp_size=14336, vocab_size=128 * 1024, num_layers=32
    )

    # a tiny model to measure the overhead
    # of piecewise cudagraph
    llama_config = LlamaConfig(
        hidden_size=40, mlp_size=80, vocab_size=128, num_layers=2
    )

    cudagraph_sizes = [1, 2, 4] + [i * 8 for i in range(1, 33)]

    eager_time = {}
    full_cudagraph_time = {}
    piecewise_cudagraph_time = {}

    pool = torch.cuda.graph_pool_handle()

    for piecewise in [False, True]:
        if piecewise:
            compilation_config = CompilationConfig(
                mode=CompilationMode.VLLM_COMPILE,
                splitting_ops=["silly::attention"],
                cudagraph_capture_sizes=cudagraph_sizes,
            )
        else:
            compilation_config = CompilationConfig(
                mode=CompilationMode.VLLM_COMPILE,
                cudagraph_capture_sizes=cudagraph_sizes,
            )

        vllm_config = VllmConfig(compilation_config=compilation_config)
        with set_current_vllm_config(vllm_config):
            model = (
                LlamaModel(config=llama_config, vllm_config=vllm_config, prefix="")
                .eval()
                .cuda()
                .to(torch.bfloat16)
            )

        B = 256  # max batch size
        input_ids = torch.randint(0, llama_config.vocab_size, (B,)).cuda()
        positions = torch.arange(B).cuda().to(torch.bfloat16)

        graphs = {}

        model(input_ids, positions)
        for b in cudagraph_sizes[::-1]:
            if not piecewise:
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph, pool=pool):
                    output = model(input_ids[:b], positions[:b])
                graphs[b] = (graph, output)
            else:
                output = model(input_ids[:b], positions[:b])
                graphs[b] = (model, output)
        for b in cudagraph_sizes:
            if piecewise:
                # noqa is for `Function definition does not bind loop variable`
                # it will be problematic if we save the created lambda function
                # and use it later, because it will look up the name `b` in the
                # enclosing scope, and the value of `b` will always be 256.
                # it is fine here, because we only use the lambda function once.
                runtime = do_bench(
                    lambda: graphs[b][0](  # noqa
                        input_ids[:b],  # noqa
                        positions[:b],  # noqa
                    )
                )
                piecewise_cudagraph_time[b] = runtime
            else:
                runtime = do_bench(lambda: graphs[b][0].replay())  # noqa
                eager_runtime = do_bench(lambda: model(input_ids[:b], positions[:b]))  # noqa
                full_cudagraph_time[b] = runtime
                eager_time[b] = eager_runtime

    # print in tabular format
    print("batch size\teager mode\tfull cudagraph\tpiecewise cudagraph")
    for b in cudagraph_sizes:
        print(
            f"{b}\t{eager_time[b]:.3f}\t{full_cudagraph_time[b]:.3f}"
            f"\t{piecewise_cudagraph_time[b]:.3f}"
        )