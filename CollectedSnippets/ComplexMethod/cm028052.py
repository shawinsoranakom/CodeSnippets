def batch_sampler_fn(batch_size, state=None, next_state=None, **kwargs):
      """Sampler fn."""
      contexts_tuples = [
          sampler(batch_size, state=state, next_state=next_state, **kwargs)
          for sampler in sampler_fns]
      contexts = [c[0] for c in contexts_tuples]
      next_contexts = [c[1] for c in contexts_tuples]
      contexts = [
          normalizer.update_apply(c) if normalizer is not None else c
          for normalizer, c in zip(self._normalizers, contexts)
      ]
      next_contexts = [
          normalizer.apply(c) if normalizer is not None else c
          for normalizer, c in zip(self._normalizers, next_contexts)
      ]
      return contexts, next_contexts