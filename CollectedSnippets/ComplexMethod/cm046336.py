def handle_yolo_solutions(args: list[str]) -> None:
    """Process YOLO solutions arguments and run the specified computer vision solutions pipeline.

    Args:
        args (list[str]): Command-line arguments for configuring and running the Ultralytics YOLO solutions.

    Examples:
        Run people counting solution with default settings:
        >>> handle_yolo_solutions(["count"])

        Run analytics with custom configuration:
        >>> handle_yolo_solutions(["analytics", "conf=0.25", "source=path/to/video.mp4"])

        Run inference with custom configuration, requires Streamlit version 1.29.0 or higher.
        >>> handle_yolo_solutions(["inference", "model=yolo26n.pt"])

    Notes:
        - Arguments can be provided in the format 'key=value' or as boolean flags
        - Available solutions are defined in SOLUTION_MAP with their respective classes and methods
        - If an invalid solution is provided, defaults to 'count' solution
        - Output videos are saved in 'runs/solution/{solution_name}' directory
        - For 'analytics' solution, frame numbers are tracked for generating analytical graphs
        - Video processing can be interrupted by pressing 'q'
        - Processes video frames sequentially and saves output in .avi format
        - If no source is specified, downloads and uses a default sample video
        - The inference solution will be launched using the 'streamlit run' command.
        - The Streamlit app file is located in the Ultralytics package directory.
    """
    from ultralytics.solutions.config import SolutionConfig

    full_args_dict = vars(SolutionConfig())  # arguments dictionary
    overrides = {}

    # check dictionary alignment
    for arg in merge_equals_args(args):
        arg = arg.lstrip("-").rstrip(",")
        if "=" in arg:
            try:
                k, v = parse_key_value_pair(arg)
                overrides[k] = v
            except (NameError, SyntaxError, ValueError, AssertionError) as e:
                check_dict_alignment(full_args_dict, {arg: ""}, e)
        elif arg in full_args_dict and isinstance(full_args_dict.get(arg), bool):
            overrides[arg] = True
    check_dict_alignment(full_args_dict, overrides)  # dict alignment

    # Get solution name
    if not args:
        LOGGER.warning("No solution name provided. i.e `yolo solutions count`. Defaulting to 'count'.")
        args = ["count"]
    if args[0] == "help":
        LOGGER.info(SOLUTIONS_HELP_MSG)
        return  # Early return for 'help' case
    elif args[0] in SOLUTION_MAP:
        solution_name = args.pop(0)  # Extract the solution name directly
    else:
        LOGGER.warning(
            f"❌ '{args[0]}' is not a valid solution. 💡 Defaulting to 'count'.\n"
            f"🚀 Available solutions: {', '.join(list(SOLUTION_MAP.keys())[:-1])}\n"
        )
        solution_name = "count"  # Default for invalid solution

    if solution_name == "inference":
        checks.check_requirements("streamlit>=1.29.0")
        LOGGER.info("💡 Loading Ultralytics live inference app...")
        subprocess.run(
            [  # Run subprocess with Streamlit custom argument
                "streamlit",
                "run",
                str(ROOT / "solutions/streamlit_inference.py"),
                "--server.headless",
                "true",
                overrides.pop("model", "yolo26n.pt"),
            ]
        )
    else:
        import cv2  # Only needed for cap and vw functionality

        from ultralytics import solutions

        solution = getattr(solutions, SOLUTION_MAP[solution_name])(is_cli=True, **overrides)  # class i.e. ObjectCounter

        cap = cv2.VideoCapture(solution.CFG["source"])  # read the video file
        if solution_name != "crop":
            # extract width, height and fps of the video file, create save directory and initialize video writer
            w, h, fps = (
                int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS)
            )
            if solution_name == "analytics":  # analytical graphs follow fixed shape for output i.e w=1920, h=1080
                w, h = 1280, 720
            save_dir = get_save_dir(SimpleNamespace(task="solutions", name="exp", exist_ok=False, project=None))
            save_dir.mkdir(parents=True, exist_ok=True)  # create the output directory i.e. runs/solutions/exp
            vw = cv2.VideoWriter(str(save_dir / f"{solution_name}.avi"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

        try:  # Process video frames
            f_n = 0  # frame number, required for analytical graphs
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break
                results = solution(frame, f_n := f_n + 1) if solution_name == "analytics" else solution(frame)
                if solution_name != "crop":
                    vw.write(results.plot_im)
                if solution.CFG["show"] and cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            cap.release()