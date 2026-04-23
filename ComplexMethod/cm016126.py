def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--launcher",
        default=False,
        action="store_true",
        help="launch workers across machines",
    )
    parser.add_argument(
        "--worker",
        default=False,
        action="store_true",
        help="launches jobs on a single machine",
    )
    parser.add_argument(
        "--runner",
        default=False,
        action="store_true",
        help="runs tests in a specific environment",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="runs a single test case",
    )
    parser.add_argument("--gpu", nargs="+", type=str, default=["t4"])
    parser.add_argument("--html", type=str, default=None)
    parser.add_argument("--golden", type=str, default=None)
    parser.add_argument("--create-golden", action="store_true")
    parser.add_argument("--dtype", type=str)
    parser.add_argument("--category", type=str)
    parser.add_argument("--function", type=str)
    parser.add_argument("--pass-type", type=str)
    parser.add_argument("--pytorch-version", type=str)
    parser.add_argument("--cuda-version", type=str)
    parser.add_argument("--mode")
    args = parser.parse_args()
    if args.runner:
        assert torch is not None  # noqa: S101
        torch.set_default_device("cuda")
        (gpu,) = args.gpu
        logging.basicConfig(
            level=logging.INFO,
            format=f"%(asctime)s - runner:{gpu}/{args.pytorch_version}/{args.cuda_version}/{args.mode} - %(message)s",
        )
        asyncio.run(runner(args))
    if args.worker:
        (gpu,) = args.gpu
        logging.basicConfig(
            level=logging.INFO, format=f"%(asctime)s - worker:{gpu} - %(message)s"
        )
        asyncio.run(worker(args))
    if args.launcher:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - launcher - %(message)s"
        )
        try:
            asyncio.run(launcher(args))
        except KeyboardInterrupt:
            log.error("Cancelled by user")
    if args.test:
        test_id = (
            f"{args.gpu[0]}/{args.pytorch_version}/{args.cuda_version}"
            f"/{args.mode}/{args.dtype}/{args.category}"
            f"/{args.function}/{args.pass_type}"
        )
        logging.basicConfig(
            level=logging.INFO,
            format=f"%(asctime)s - test:{test_id} - %(message)s",
        )
        run_test_case(args)
    if args.html:
        format_results_to_html(args.html)