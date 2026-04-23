def setUp(self):
  if not is_torch_greater_or_equal_than_2_3:
    self.skipTest("torch >= 2.3 is required")

    set_seed(0)
    self.model = AutoModelForCausalLM.from_pretrained("hf-internal-testing/tiny-random-LlamaForCausalLM")
    self.model.eval()

    self.model.generation_config = GenerationConfig(
      use_cache=True,
      cache_implementation="static",
      cache_config={"batch_size": 1, "max_cache_len": 32, "device": "cpu"},
    )

    self.input_ids = torch.tensor([[1, 2, 3]], dtype=torch.long)
    self.inputs_embeds = torch.randn(1, 3, self.model.config.hidden_size)
    self.cache_position = torch.arange(3, dtype=torch.long)
