def __init__(self, configs: Configs):
        # Get the device
        self.device = torch.device('cpu')
        if torch.cuda.is_available():
            self.device = torch.device('cuda:0')
        # Initialize the dataset
        self.dataset = TinyShakespeareDataset(configs.seq_len)
        # Initialize the dataloader
        self.dataloader = DataLoader(self.dataset,
                                     batch_size=configs.batch_size,
                                     collate_fn=transpose_batch,
                                     shuffle=True)

        # FFN with Gated Linear Unit
        # $$FFN_{GLU}(x)(x, W_1, V, W_2) = (\sigma(x W_1) \otimes x V) W_2$$
        if configs.glu_variant == 'GLU':
            ffn = FeedForward(configs.d_model, configs.d_ff, configs.dropout, nn.Sigmoid(), True, False, False, False)
        # FFN with Bilinear hidden layer
        # $$FFN_{Bilinear}(x)(x, W_1, V, W_2) = (x W_1 \otimes x V) W_2$$
        elif configs.glu_variant == 'Bilinear':
            ffn = FeedForward(configs.d_model, configs.d_ff, configs.dropout, nn.Identity(), True, False, False, False)
        # FFN with ReLU gate
        # $$FFN_{ReGLU}(x)(x, W_1, V, W_2) = (\max(0, x W_1) \otimes x V) W_2$$
        elif configs.glu_variant == 'ReGLU':
            ffn = FeedForward(configs.d_model, configs.d_ff, configs.dropout, nn.ReLU(), True, False, False, False)
        # FFN with GELU gate
        # $$FFN_{GEGLU}(x)(x, W_1, V, W_2) = (\text{GELU}(x W_1) \otimes x V) W_2$$
        elif configs.glu_variant == 'GEGLU':
            ffn = FeedForward(configs.d_model, configs.d_ff, configs.dropout, nn.GELU(), True, False, False, False)
        # FFN with Swish gate
        # $$FFN_{SwiGLU}(x)(x, W_1, V, W_2) = (\text{Swish}_1(x W_1) \otimes x V) W_2$$
        # where $\text{Swish}_\beta(x) = x \sigma(\beta x)$
        elif configs.glu_variant == 'SwiGLU':
            ffn = FeedForward(configs.d_model, configs.d_ff, configs.dropout, nn.SiLU(), True, False, False, False)
        # FFN with ReLU activation
        # $$FFN_{ReLU}(x)(x, W_1, W_2, b_1, b_2) = \text{ReLU}_1(x W_1 + b_1) W_2 + b_2$$
        elif configs.glu_variant == 'ReLU':
            ffn = FeedForward(configs.d_model, configs.d_ff, configs.dropout, nn.ReLU())
        # FFN with ReLU activation
        # $$FFN_{GELU}(x)(x, W_1, W_2, b_1, b_2) = \text{GELU}_1(x W_1 + b_1) W_2 + b_2$$
        elif configs.glu_variant == 'GELU':
            ffn = FeedForward(configs.d_model, configs.d_ff, configs.dropout, nn.GELU())
        else:
            raise ValueError(f'Unknown variant {configs.glu_variant}')

        # Number of different characters
        n_chars = len(self.dataset.stoi)

        # Initialize [Multi-Head Attention module](../mha.html)
        mha = MultiHeadAttention(configs.n_heads, configs.d_model, configs.dropout)
        # Initialize the [Transformer Block](../models.html#TransformerLayer)
        transformer_layer = TransformerLayer(d_model=configs.d_model, self_attn=mha, src_attn=None,
                                             feed_forward=ffn, dropout_prob=configs.dropout)
        # Initialize the model with an
        # [embedding layer](../models.html#EmbeddingsWithPositionalEncoding)
        # (with fixed positional encoding)
        # [transformer encoder](../models.html#Encoder) and
        # a linear layer to generate logits.
        self.model = AutoregressiveModel(EmbeddingsWithPositionalEncoding(configs.d_model, n_chars),
                                         Encoder(transformer_layer, configs.n_layers),
                                         nn.Linear(configs.d_model, n_chars))

        # Move the model to the current device
        self.model.to(self.device)

        # Initialize [Noam optimizer](../../optimizers/noam.html)
        self.optimizer = Noam(self.model.parameters(), lr=1.0, warmup=2_000, d_model=configs.d_model)

        # Cross-entropy loss
        self.loss_func = nn.CrossEntropyLoss()
        # Number of training epochs;
        # *note that our dataset definition repeats the data `seq_len` times in a single epoch*
        self.epochs = configs.epochs
        # Gradient clipping norm
        self.grad_norm_clip = configs.grad_norm_clip

        # Set tracker configurations
        tracker.set_scalar("loss.*", True)