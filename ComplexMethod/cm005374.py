def print_model_load(self, model: str):
        response = requests.post(f"{self.base_url.rstrip('/')}/load_model", json={"model": model}, stream=True)
        response.raise_for_status()

        class StatsColumn(ProgressColumn):
            def render(self, task):
                if not task.total:
                    return Text("")

                if task.fields.get("unit") == "bytes":
                    done = filesize.decimal(int(task.completed))
                    tot = filesize.decimal(int(task.total))
                    speed = f"  {filesize.decimal(int(task.speed))}/s" if task.speed else ""

                    if task.time_remaining is not None:
                        eta = f"  {int(task.time_remaining // 60)}:{int(task.time_remaining % 60):02d}"
                    else:
                        eta = ""

                    return Text(f"{done}/{tot}{speed}{eta}", style="progress.download")
                return Text(f"{int(task.completed)}/{int(task.total)}")

        stage_labels = {
            "processor": "Loading processor",
            "config": "Loading config",
            "download": "Downloading files",
            "weights": "Loading into memory",
        }

        # Include the model name prefix in descriptions only when the terminal is wide enough.
        # The bar, stats, and elapsed columns need ~70 chars; the model prefix needs len(model)+5.
        show_model_prefix = self._console.width >= len(model) + 5 + 70

        def _label(stage_key):
            stage_text = stage_labels.get(stage_key, stage_key)
            if show_model_prefix:
                return f"{model}  →  {stage_text}"
            return stage_text

        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(bar_width=40),
            StatsColumn(),
            TimeElapsedColumn(),
            console=self._console,
        )
        task_id = progress.add_task(_label("processor"), total=None)
        cached = False

        with Live(progress, console=self._console, transient=True):
            for line in response.iter_lines():
                if not line or not line.startswith(b"data: "):
                    continue
                event = json.loads(line[6:])
                status = event.get("status")

                if status == "ready":
                    cached = event.get("cached", False)
                    break

                if status == "error":
                    raise RuntimeError(event.get("message", "Unknown error"))

                if status == "loading":
                    stage = event.get("stage")
                    prog = event.get("progress")
                    label = _label(stage)

                    if prog:
                        unit = "bytes" if stage == "download" else "items"
                        progress.update(
                            task_id, description=label, completed=prog["current"], total=prog.get("total"), unit=unit
                        )
                    else:
                        progress.update(task_id, description=label, completed=0, total=None)

        if cached:
            self._console.print(Markdown(f"_*{model} was already loaded.*_"))
        else:
            self._console.print(Markdown(f"_*{model} is warm.*_"))
        self._console.print()