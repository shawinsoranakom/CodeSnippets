 class TinyGPT2WithUninitializedWeights(GPT2PreTrainedModel):
            def __init__(self, config):
                super().__init__(config)
                self.transformer = AutoModel.from_pretrained(GPT2_TINY, config=config)
                self.new_head = torch.nn.Linear(config.hidden_size, config.vocab_size, bias=True)

            def forward(self, *args, **kwargs):
                transformer_outputs = self.transformer(*args, **kwargs)
                hidden_states = transformer_outputs[0]
                return self.new_head(hidden_states).float()

            def _init_weights(self, module):
                super()._init_weights(module)
                if module is self.new_head:
                    nn.init.constant_(self.new_head.weight.data, -100.0)
                    nn.init.constant_(self.new_head.bias.data, 100.0)
