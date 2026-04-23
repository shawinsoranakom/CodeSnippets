def model_training_evaluation(
    backend, train_dataloader, eval_dataloader, model, optimizer, num_epochs, evaluation
):
    model.to(device)
    model.train()
    loss_history = []
    if not backend:
        # Run with native Pytorch
        opt_training_iter_fn = training_iter_fn
    else:
        # Support backends: eager, aot_eager, aot_nvfuser and inductor
        opt_training_iter_fn = torch._dynamo.optimize(backend)(training_iter_fn)
    for epoch in range(num_epochs):
        running_loss = 0.0
        for i, batch in enumerate(train_dataloader, 0):
            batch = {k: v.to(device) for k, v in batch.items()}
            loss = opt_training_iter_fn(batch, model, optimizer)
            running_loss += loss.item()
            if i % 100 == 99:
                loss_history.append(running_loss / 100)
                running_loss = 0.0

    if evaluation:
        metric = load_metric("accuracy")
        model.eval()
        if not backend:
            opt_model = model
        else:
            opt_model = torch._dynamo.optimize(backend)(model)
        for batch in eval_dataloader:
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.no_grad():
                outputs = opt_model(**batch)

            logits = outputs.logits
            predictions = torch.argmax(logits, dim=-1)
            metric.add_batch(predictions=predictions, references=batch["labels"])

        return loss_history, metric.compute()
    else:
        return loss_history, None