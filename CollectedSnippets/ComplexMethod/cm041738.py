def get_trainer_info(lang: str, output_path: os.PathLike, do_train: bool) -> tuple[str, "gr.Slider", dict[str, Any]]:
    r"""Get training infomation for monitor.

    If do_train is True:
        Inputs: top.lang, train.output_path
        Outputs: train.output_box, train.progress_bar, train.loss_viewer, train.swanlab_link
    If do_train is False:
        Inputs: top.lang, eval.output_path
        Outputs: eval.output_box, eval.progress_bar, None, None
    """
    running_log = ""
    running_progress = gr.Slider(visible=False)
    running_info = {}

    running_log_path = os.path.join(output_path, RUNNING_LOG)
    if os.path.isfile(running_log_path):
        with open(running_log_path, encoding="utf-8") as f:
            running_log = "```\n" + f.read()[-20000:] + "\n```\n"  # avoid lengthy log

    trainer_log_path = os.path.join(output_path, TRAINER_LOG)
    if os.path.isfile(trainer_log_path):
        trainer_log: list[dict[str, Any]] = []
        with open(trainer_log_path, encoding="utf-8") as f:
            for line in f:
                trainer_log.append(json.loads(line))

        if len(trainer_log) != 0:
            latest_log = trainer_log[-1]
            percentage = latest_log["percentage"]
            label = "Running {:d}/{:d}: {} < {}".format(
                latest_log["current_steps"],
                latest_log["total_steps"],
                latest_log["elapsed_time"],
                latest_log["remaining_time"],
            )
            running_progress = gr.Slider(label=label, value=percentage, visible=True)

            if do_train and is_matplotlib_available():
                running_info["loss_viewer"] = gr.Plot(gen_loss_plot(trainer_log))

    swanlab_config_path = os.path.join(output_path, SWANLAB_CONFIG)
    if os.path.isfile(swanlab_config_path):
        with open(swanlab_config_path, encoding="utf-8") as f:
            swanlab_public_config = json.load(f)
            swanlab_link = swanlab_public_config["cloud"]["experiment_url"]
            if swanlab_link is not None:
                running_info["swanlab_link"] = gr.Markdown(
                    ALERTS["info_swanlab_link"][lang] + swanlab_link, visible=True
                )

    return running_log, running_progress, running_info