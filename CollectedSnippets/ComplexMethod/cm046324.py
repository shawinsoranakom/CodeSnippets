def __call__(self, iterations: int = 10, cleanup: bool = True):
        """Execute the hyperparameter evolution process when the Tuner instance is called.

        This method iterates through the specified number of iterations, performing the following steps:
        1. Sync MongoDB results to local NDJSON (if using distributed mode)
        2. Mutate hyperparameters using the best previous results or defaults
        3. Train a YOLO model with the mutated hyperparameters
        4. Log fitness scores and hyperparameters to MongoDB and/or NDJSON
        5. Track the best performing configuration across all iterations

        Args:
            iterations (int): The number of generations to run the evolution for.
            cleanup (bool): Whether to delete iteration weights to reduce storage space during tuning.
        """
        t0 = time.time()
        self.tune_dir.mkdir(parents=True, exist_ok=True)
        (self.tune_dir / "weights").mkdir(parents=True, exist_ok=True)
        best_save_dirs = {}

        # Sync MongoDB to local NDJSON at startup for proper resume logic
        if self.mongodb:
            self._sync_mongodb_to_file()

        start = 0
        if self.tune_file.exists():
            start = len(self._load_local_results())
            LOGGER.info(f"{self.prefix}Resuming tuning run {self.tune_dir} from iteration {start + 1}...")
        for i in range(start, iterations):
            # Linearly decay sigma from 0.2 → 0.1 over first 300 iterations
            frac = min(i / 300.0, 1.0)
            sigma_i = 0.2 - 0.1 * frac

            # Mutate hyperparameters
            mutated_hyp = self._mutate(sigma=sigma_i)
            LOGGER.info(f"{self.prefix}Starting iteration {i + 1}/{iterations} with hyperparameters: {mutated_hyp}")

            train_args = {**vars(self.args), **mutated_hyp}
            data = train_args.pop("data")
            if not isinstance(data, (list, tuple)):
                data = [data]
            dataset_names = self._dataset_names(data)
            save_dir = (
                [get_save_dir(get_cfg(train_args))]
                if len(data) == 1
                else [get_save_dir(get_cfg(train_args), name=name) for name in dataset_names]
            )
            weights_dir = [s / "weights" for s in save_dir]
            metrics = {}
            all_fitness = []
            dataset_metrics = {}
            for j, (d, dataset) in enumerate(zip(data, dataset_names)):
                metrics_i = {}
                try:
                    train_args["data"] = d
                    train_args["save_dir"] = str(save_dir[j])  # pass save_dir to subprocess to ensure same path is used
                    # Train YOLO model with mutated hyperparameters (run in subprocess to avoid dataloader hang)
                    launch = [
                        __import__("sys").executable,
                        "-m",
                        "ultralytics.cfg.__init__",
                    ]  # workaround yolo not found
                    cmd = [*launch, "train", *(f"{k}={v}" for k, v in train_args.items())]
                    return_code = subprocess.run(cmd, check=True).returncode
                    ckpt_file = weights_dir[j] / ("best.pt" if (weights_dir[j] / "best.pt").exists() else "last.pt")
                    metrics_i = torch_load(ckpt_file)["train_metrics"]
                    metrics = metrics_i
                    assert return_code == 0, "training failed"

                    # Cleanup
                    time.sleep(1)
                    gc.collect()
                    torch.cuda.empty_cache()

                except Exception as e:
                    LOGGER.error(f"training failure for hyperparameter tuning iteration {i + 1}\n{e}")

                # Save results - MongoDB takes precedence
                dataset_metrics[dataset] = metrics_i or {"fitness": 0.0}
                all_fitness.append(dataset_metrics[dataset].get("fitness") or 0.0)
            fitness = sum(all_fitness) / len(all_fitness)
            result = self._result_record(
                i + 1,
                fitness,
                mutated_hyp,
                dataset_metrics,
                {dataset: str(s) for dataset, s in zip(dataset_names, save_dir)},
            )
            stop_after_iteration = False
            if self.mongodb:
                self._save_to_mongodb(fitness, mutated_hyp, metrics, dataset_metrics, i + 1)
                self._sync_mongodb_to_file()
                total_mongo_iterations = self.collection.count_documents({})
                if total_mongo_iterations >= iterations:
                    stop_after_iteration = True
            else:
                self._save_local_result(result)

            # Get best results
            results = self._load_local_results()
            x = self._local_results_to_array(results)
            fitness = x[:, 0]  # first column
            best_idx = fitness.argmax()
            best_result = results[best_idx]
            current_best_save_dirs = best_result.get("save_dirs", {})
            best_is_current = best_idx == i
            if best_is_current:
                if cleanup:
                    for s in best_save_dirs.values():
                        if s not in current_best_save_dirs.values():
                            shutil.rmtree(s, ignore_errors=True)
                if len(data) == 1:
                    for ckpt in weights_dir[0].glob("*.pt"):
                        shutil.copy2(ckpt, self.tune_dir / "weights")
                best_save_dirs = current_best_save_dirs
            elif cleanup:
                for s in save_dir:
                    shutil.rmtree(s, ignore_errors=True)  # remove iteration dirs to reduce storage space
                best_save_dirs = current_best_save_dirs

            # Plot tune results
            plot_tune_results(str(self.tune_file))

            # Save and print tune results
            header = (
                f"{self.prefix}{i + 1}/{iterations} iterations complete ✅ ({time.time() - t0:.2f}s)\n"
                f"{self.prefix}Results saved to {colorstr('bold', self.tune_dir)}\n"
                f"{self.prefix}Best fitness={fitness[best_idx]} observed at iteration {best_idx + 1}\n"
                f"{self.prefix}Best fitness metrics are {self._best_metrics(best_result)}\n"
                f"{self.prefix}Best fitness model is "
                f"{self.tune_dir / 'weights' if len(best_result.get('datasets', {})) == 1 else 'not saved for multi-dataset tuning'}"
            )
            LOGGER.info("\n" + header)
            data = {k: int(v) if k in CFG_INT_KEYS else float(v) for k, v in zip(self.space.keys(), x[best_idx, 1:])}
            YAML.save(
                self.tune_dir / "best_hyperparameters.yaml",
                data=data,
                header=remove_colorstr(header.replace(self.prefix, "# ")) + "\n",
            )
            YAML.print(self.tune_dir / "best_hyperparameters.yaml")
            if stop_after_iteration:
                LOGGER.info(
                    f"{self.prefix}Target iterations ({iterations}) reached in MongoDB ({total_mongo_iterations}). Stopping."
                )
                break