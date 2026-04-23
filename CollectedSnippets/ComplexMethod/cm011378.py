def run(rank, world_size):
    # Set up world pg
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "12355"

    dist.init_process_group("cpu:gloo,cuda:nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

    model, optim = _init_model(rank, world_size)
    state_dict = {"model": model, "optim": optim}
    loss_calc = torch.nn.BCELoss()

    f = None
    # pyrefly: ignore [bad-assignment]
    for epoch in range(NUM_EPOCHS):
        try:
            torch.manual_seed(epoch)
            x, y = _input()

            loss = loss_calc(model(x), y)

            _print(f"{epoch=} {loss=}")

            loss.backward()
            optim.step()
            optim.zero_grad()

            if epoch % SAVE_PERIOD == 0:
                if f is not None:
                    if not isinstance(f, Future):
                        raise AssertionError("f should be a Future instance")
                    f.result()
                f = dcp.state_dict_saver.async_save(
                    state_dict, checkpoint_id=CHECKPOINT_DIR
                )

            if FAULT_PERIOD > 0 and epoch % FAULT_PERIOD == 0:
                raise InjectedException("Fault injection!")

        except InjectedException as e:
            dist.barrier()

            _print("Trainer encountered exception:")
            traceback.print_tb(e.__traceback__)

            _print("Reloading model from last checkpoint!")
            if f is not None:
                if not isinstance(f, Future):
                    raise AssertionError("f should be a Future instance") from None
                f.result()
            dcp.load(state_dict)