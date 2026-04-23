def setUpClass(cls):
    # Make model small
    FLAGS.batch_size = 2
    FLAGS.num_timesteps = 3
    FLAGS.embedding_dims = 4
    FLAGS.rnn_num_layers = 2
    FLAGS.rnn_cell_size = 4
    FLAGS.cl_num_layers = 2
    FLAGS.cl_hidden_size = 4
    FLAGS.vocab_size = 10

    # Set input/output flags
    FLAGS.data_dir = tempfile.mkdtemp()

    # Build and write sequence files.
    vocab_ids = _build_random_vocabulary(FLAGS.vocab_size)
    seqs = [_build_random_sequence(vocab_ids) for _ in range(5)]
    seqs_label = [
        data.build_labeled_sequence(seq, random.choice([True, False]))
        for seq in seqs
    ]
    seqs_lm = [data.build_lm_sequence(seq) for seq in seqs]
    seqs_ae = [data.build_seq_ae_sequence(seq) for seq in seqs]
    seqs_rev = [data.build_reverse_sequence(seq) for seq in seqs]
    seqs_bidir = [
        data.build_bidirectional_seq(seq, rev)
        for seq, rev in zip(seqs, seqs_rev)
    ]
    seqs_bidir_label = [
        data.build_labeled_sequence(bd_seq, random.choice([True, False]))
        for bd_seq in seqs_bidir
    ]

    filenames = [
        data.TRAIN_CLASS, data.TRAIN_LM, data.TRAIN_SA, data.TEST_CLASS,
        data.TRAIN_REV_LM, data.TRAIN_BD_CLASS, data.TEST_BD_CLASS
    ]
    seq_lists = [
        seqs_label, seqs_lm, seqs_ae, seqs_label, seqs_rev, seqs_bidir,
        seqs_bidir_label
    ]
    for fname, seq_list in zip(filenames, seq_lists):
      with tf.python_io.TFRecordWriter(
          os.path.join(FLAGS.data_dir, fname)) as writer:
        for seq in seq_list:
          writer.write(seq.seq.SerializeToString())

    # Write vocab.txt and vocab_freq.txt
    vocab_freqs = _build_vocab_frequencies(seqs, vocab_ids)
    ordered_vocab_freqs = sorted(
        vocab_freqs.items(), key=operator.itemgetter(1), reverse=True)
    with open(os.path.join(FLAGS.data_dir, 'vocab.txt'), 'w') as vocab_f:
      with open(os.path.join(FLAGS.data_dir, 'vocab_freq.txt'), 'w') as freq_f:
        for word, freq in ordered_vocab_freqs:
          vocab_f.write('{}\n'.format(word))
          freq_f.write('{}\n'.format(freq))