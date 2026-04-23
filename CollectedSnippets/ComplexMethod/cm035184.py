def make_input(ser_inputs, ser_results):
    entities_labels = {"HEADER": 0, "QUESTION": 1, "ANSWER": 2}
    batch_size, max_seq_len = ser_inputs[0].shape[:2]
    entities = ser_inputs[8][0]
    ser_results = ser_results[0]
    assert len(entities) == len(ser_results)

    # entities
    start = []
    end = []
    label = []
    entity_idx_dict = {}
    for i, (res, entity) in enumerate(zip(ser_results, entities)):
        if res["pred"] == "O":
            continue
        entity_idx_dict[len(start)] = i
        start.append(entity["start"])
        end.append(entity["end"])
        label.append(entities_labels[res["pred"]])

    entities = np.full([max_seq_len + 1, 3], fill_value=-1, dtype=np.int64)
    entities[0, 0] = len(start)
    entities[1 : len(start) + 1, 0] = start
    entities[0, 1] = len(end)
    entities[1 : len(end) + 1, 1] = end
    entities[0, 2] = len(label)
    entities[1 : len(label) + 1, 2] = label

    # relations
    head = []
    tail = []
    for i in range(len(label)):
        for j in range(len(label)):
            if label[i] == 1 and label[j] == 2:
                head.append(i)
                tail.append(j)

    relations = np.full([len(head) + 1, 2], fill_value=-1, dtype=np.int64)
    relations[0, 0] = len(head)
    relations[1 : len(head) + 1, 0] = head
    relations[0, 1] = len(tail)
    relations[1 : len(tail) + 1, 1] = tail

    entities = np.expand_dims(entities, axis=0)
    entities = np.repeat(entities, batch_size, axis=0)
    relations = np.expand_dims(relations, axis=0)
    relations = np.repeat(relations, batch_size, axis=0)

    # remove ocr_info segment_offset_id and label in ser input
    if isinstance(ser_inputs[0], paddle.Tensor):
        entities = paddle.to_tensor(entities)
        relations = paddle.to_tensor(relations)
    ser_inputs = ser_inputs[:5] + [entities, relations]

    entity_idx_dict_batch = []
    for b in range(batch_size):
        entity_idx_dict_batch.append(entity_idx_dict)
    return ser_inputs, entity_idx_dict_batch