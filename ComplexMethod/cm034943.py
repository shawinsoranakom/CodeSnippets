def __init__(
        self,
        enc_bi_rnn=False,
        enc_drop_rnn=0.1,
        enc_gru=False,
        d_model=512,
        d_enc=512,
        mask=True,
        **kwargs,
    ):
        super().__init__()
        assert isinstance(enc_bi_rnn, bool)
        assert isinstance(enc_drop_rnn, (int, float))
        assert 0 <= enc_drop_rnn < 1.0
        assert isinstance(enc_gru, bool)
        assert isinstance(d_model, int)
        assert isinstance(d_enc, int)
        assert isinstance(mask, bool)

        self.enc_bi_rnn = enc_bi_rnn
        self.enc_drop_rnn = enc_drop_rnn
        self.mask = mask

        # LSTM Encoder
        if enc_bi_rnn:
            direction = "bidirectional"
        else:
            direction = "forward"
        kwargs = dict(
            input_size=d_model,
            hidden_size=d_enc,
            num_layers=2,
            time_major=False,
            dropout=enc_drop_rnn,
            direction=direction,
        )
        if enc_gru:
            self.rnn_encoder = nn.GRU(**kwargs)
        else:
            self.rnn_encoder = nn.LSTM(**kwargs)

        # global feature transformation
        encoder_rnn_out_size = d_enc * (int(enc_bi_rnn) + 1)
        self.linear = nn.Linear(encoder_rnn_out_size, encoder_rnn_out_size)