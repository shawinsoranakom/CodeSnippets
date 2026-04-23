def main():
    parser = ArgumentParser("Main script to benchmark functional API of the autograd.")
    parser.add_argument(
        "--output", type=str, default="", help="Text file where to write the output"
    )
    parser.add_argument("--num-iters", type=int, default=10)
    parser.add_argument(
        "--gpu",
        type=int,
        default=-2,
        help="GPU to use, -1 for CPU and -2 for auto-detect",
    )
    parser.add_argument(
        "--run-slow-tasks", action="store_true", help="Run even the slow tasks"
    )
    parser.add_argument(
        "--model-filter",
        type=str,
        default="",
        help="Only run the models in this filter",
    )
    parser.add_argument(
        "--task-filter", type=str, default="", help="Only run the tasks in this filter"
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=10,
        help="Number of concurrent threads to use when running on cpu",
    )
    parser.add_argument("--seed", type=int, default=0, help="The random seed to use.")
    args = parser.parse_args()

    results: TimingResultType = defaultdict(defaultdict)
    torch.set_num_threads(args.num_threads)
    torch.set_num_interop_threads(args.num_threads)

    # This automatically seed cuda if it is available
    torch.manual_seed(args.seed)

    if args.gpu == -2:
        args.gpu = 0 if torch.cuda.is_available() else -1

    for name, model_getter, recommended_tasks, unsupported_tasks in MODELS:
        if args.model_filter and name not in args.model_filter:
            continue
        tasks = ALL_TASKS if args.run_slow_tasks else recommended_tasks
        for task in tasks:
            if task in unsupported_tasks:
                continue
            if args.task_filter and task not in args.task_filter:
                continue
            runtimes = run_model(model_getter, args, task)

            runtimes = torch.tensor(runtimes)
            mean, var = runtimes.mean(), runtimes.var()
            results[name][task] = (mean.item(), var.item())
            print(f"Results for model {name} on task {task}: {mean}s (var: {var})")

            if has_functorch:
                try:
                    runtimes = run_model(
                        model_getter, args, task, run_once_fn=run_once_functorch
                    )
                except RuntimeError as e:
                    print(
                        f"Failed model using Functorch: {name}, task: {task}, Error message: \n\t",
                        e,
                    )
                    continue

                runtimes = torch.tensor(runtimes)
                mean, var = runtimes.mean(), runtimes.var()
                results[name][f"functorch {task}"] = (mean.item(), var.item())
                print(
                    f"Results for model {name} on task {task} using Functorch: {mean}s (var: {var})"
                )

    if args.output:
        with open(args.output, "w") as f:
            f.write(to_markdown_table(results))