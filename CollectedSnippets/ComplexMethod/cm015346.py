def f(device, reset_storage=False):
            torch.manual_seed(2023)

            if device == "lazy":
                metrics.reset()

            class Model(torch.nn.Module):
                def __init__(self) -> None:
                    super().__init__()
                    self.fc1 = torch.nn.Linear(4, 2, bias=False)

                def forward(self, x):
                    return x @ self.fc1.weight.transpose(0, 1)

            with torch.device(device):
                model = Model()

                if device == "lazy":
                    if reset_storage:
                        torch._C._unsafe_reset_storage(model.fc1.weight)

                    torch._lazy.mark_step()

                    sync_tensors = metrics.counter_value("SyncedTensorsWithIR")
                    if reset_storage:
                        if sync_tensors != 1:
                            raise AssertionError(
                                f"Expected 1 synced tensor, got {sync_tensors}"
                            )
                    else:
                        # There is an extra tensor being unnecessarily synced if
                        # the functional storage is not reset.
                        if sync_tensors != 2:
                            raise AssertionError(
                                f"Expected 2 synced tensors, got {sync_tensors}"
                            )

                x = torch.ones(4)
                out = model(x)

                if device == "lazy":
                    torch._lazy.mark_step()

                return out