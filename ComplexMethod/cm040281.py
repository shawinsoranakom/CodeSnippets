def test_early_stopping_final_weights_when_restoring_model_weights(self):
        class DummyModel:
            def __init__(self):
                self.stop_training = False
                self.weights = -1

            def get_weights(self):
                return self.weights

            def set_weights(self, weights):
                self.weights = weights

            def set_weight_to_epoch(self, epoch):
                self.weights = epoch

        early_stop = callbacks.EarlyStopping(
            monitor="val_loss", patience=2, restore_best_weights=True
        )
        early_stop.set_model(DummyModel())
        losses = [0.2, 0.15, 0.1, 0.11, 0.12]
        # The best configuration is in the epoch 2 (loss = 0.1000).
        epochs_trained = 0
        early_stop.on_train_begin()
        for epoch in range(len(losses)):
            epochs_trained += 1
            early_stop.model.set_weight_to_epoch(epoch=epoch)
            early_stop.on_epoch_end(epoch, logs={"val_loss": losses[epoch]})
            if early_stop.model.stop_training:
                break
        early_stop.on_train_end()
        # The best configuration is in epoch 2 (loss = 0.1000),
        # and while patience = 2, we're restoring the best weights,
        # so we end up at the epoch with the best weights, i.e. epoch 2
        self.assertEqual(early_stop.model.get_weights(), 2)

        # Check early stopping when no model beats the baseline.
        early_stop = callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            baseline=0.5,
            restore_best_weights=True,
        )
        early_stop.set_model(DummyModel())
        losses = [0.9, 0.8, 0.7, 0.71, 0.72, 0.73]
        # The best configuration is in the epoch 2 (loss = 0.7000).
        epochs_trained = 0
        early_stop.on_train_begin()
        for epoch in range(len(losses)):
            epochs_trained += 1
            early_stop.model.set_weight_to_epoch(epoch=epoch)
            early_stop.on_epoch_end(epoch, logs={"val_loss": losses[epoch]})
            if early_stop.model.stop_training:
                break
        early_stop.on_train_end()
        # No epoch improves on the baseline, so we should train for only 5
        # epochs, and restore the second model.
        self.assertEqual(epochs_trained, 5)
        self.assertEqual(early_stop.model.get_weights(), 2)

        # Check weight restoration when another callback requests a stop.
        early_stop = callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            baseline=0.5,
            restore_best_weights=True,
        )
        early_stop.set_model(DummyModel())
        losses = [0.9, 0.8, 0.7, 0.71, 0.72, 0.73]
        # The best configuration is in the epoch 2 (loss = 0.7000).
        epochs_trained = 0
        early_stop.on_train_begin()
        for epoch in range(len(losses)):
            epochs_trained += 1
            early_stop.model.set_weight_to_epoch(epoch=epoch)
            early_stop.on_epoch_end(epoch, logs={"val_loss": losses[epoch]})
            if epoch == 3:
                early_stop.model.stop_training = True
            if early_stop.model.stop_training:
                break
        early_stop.on_train_end()
        # We should restore the second model.
        self.assertEqual(epochs_trained, 4)
        self.assertEqual(early_stop.model.get_weights(), 2)