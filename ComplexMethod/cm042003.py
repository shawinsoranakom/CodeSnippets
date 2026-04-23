def fit(self, df: pd.DataFrame):
        feats = [f for f in df.columns if f != self.label_col]
        for col in df.columns:
            if df[col].isnull().sum() / df.shape[0] == 1:
                feats.remove(col)

            if df[col].nunique() == 1:
                feats.remove(col)

            if df.loc[df[col] == np.inf].shape[0] != 0 or df.loc[df[col] == np.inf].shape[0] != 0:
                feats.remove(col)

            if is_object_dtype(df[col]) and df[col].nunique() == df.shape[0]:
                feats.remove(col)

        self.feats = feats