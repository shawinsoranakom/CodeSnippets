def __iter__(self):
        size = None
        all_buffer = []
        filter_res = []
        # pyrefly: ignore [bad-assignment]
        for df in self.source_datapipe:
            if size is None:
                size = len(df.index)
            for i in range(len(df.index)):
                all_buffer.append(df[i : i + 1])
                filter_res.append(self.filter_fn(df.iloc[i]))

        buffer = []
        for df, res in zip(all_buffer, filter_res, strict=True):
            if res:
                buffer.append(df)
                if len(buffer) == size:
                    yield df_wrapper.concat(buffer)
                    buffer = []
        if buffer:
            yield df_wrapper.concat(buffer)