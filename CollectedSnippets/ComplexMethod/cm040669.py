def test_steps_per_execution_steps_per_epoch(
        self, steps_per_epoch_test, mode
    ):
        batch_size = 8
        epochs = 2
        steps_per_execution = 2
        num_batches = 5 * steps_per_execution
        data_size = num_batches * batch_size

        if steps_per_epoch_test == "match_one_epoch":
            steps_per_epoch = num_batches
        elif steps_per_epoch_test == "match_multi_epoch":
            steps_per_epoch = num_batches // steps_per_execution
        elif steps_per_epoch_test == "not_match_too_low":
            steps_per_epoch = num_batches - steps_per_execution
        elif steps_per_epoch_test == "not_match_but_high_enough":
            steps_per_epoch = num_batches + steps_per_execution

        x = np.ones((data_size, 4))
        y = np.ones((data_size, 1))

        model = ExampleModel(units=1)
        model.compile(
            loss="mse",
            optimizer="sgd",
            metrics=[EpochAgnosticMeanSquaredError()],
            steps_per_execution=steps_per_execution,
            run_eagerly=(mode == "eager"),
            jit_compile=(mode == "jit"),
        )
        step_observer = StepObserver()

        model.fit(
            x=x,
            y=y,
            batch_size=batch_size,
            epochs=epochs,
            steps_per_epoch=steps_per_epoch,
            callbacks=[step_observer],
            verbose=0,
        )
        if steps_per_epoch_test != "not_match_too_low":
            training_batch_count = (
                epochs
                * min(steps_per_epoch, num_batches)
                // steps_per_execution
            )
        else:
            complete_epochs = (num_batches // steps_per_execution) // (
                steps_per_epoch // steps_per_execution
            )
            remaining_steps = (num_batches // steps_per_execution) % (
                steps_per_epoch // steps_per_execution
            )
            steps_cycles = [
                complete_epochs * steps_per_epoch // steps_per_execution,
                remaining_steps,
            ] * epochs
            steps_per_epochs = steps_cycles[:epochs]
            training_batch_count = sum(steps_per_epochs)

        self.assertEqual(step_observer.begin_count, training_batch_count)
        self.assertEqual(step_observer.end_count, step_observer.begin_count)
        self.assertEqual(step_observer.epoch_begin_count, epochs)
        self.assertEqual(
            step_observer.epoch_end_count, step_observer.epoch_begin_count
        )

        if steps_per_epoch_test != "not_match_too_low":
            model_2 = ExampleModel(units=1)
            model_2.compile(
                loss="mse",
                optimizer="sgd",
                metrics=[EpochAgnosticMeanSquaredError()],
                steps_per_execution=1,
                run_eagerly=(mode == "eager"),
                jit_compile=(mode == "jit"),
            )
            step_observer_2 = StepObserver()

            if steps_per_epoch_test in (
                "not_match_but_high_enough",
                "match_one_epoch",
            ):
                model_2_epochs = epochs
            else:
                model_2_epochs = 1

            model_2.fit(
                x=x,
                y=y,
                batch_size=batch_size,
                epochs=model_2_epochs,
                callbacks=[step_observer_2],
                verbose=0,
            )

            losses = step_observer.batch_loss_history
            losses_2 = step_observer_2.batch_loss_history[
                steps_per_execution - 1 :: steps_per_execution
            ]
            self.assertAllClose(losses, losses_2)
            self.assertAllClose(model.get_weights(), model_2.get_weights())
            self.assertAllClose(
                model.predict(x, batch_size=batch_size),
                model_2.predict(x, batch_size=batch_size),
            )
            self.assertAllClose(model.evaluate(x, y), model_2.evaluate(x, y))