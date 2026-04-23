def table(self, data: "Data" = None) -> "DeltaGenerator":
        """Display a static table.

        This differs from `st.dataframe` in that the table in this case is
        static: its entire contents are laid out directly on the page.

        Parameters
        ----------
        data : pandas.DataFrame, pandas.Styler, pyarrow.Table, numpy.ndarray, pyspark.sql.DataFrame, snowflake.snowpark.dataframe.DataFrame, snowflake.snowpark.table.Table, Iterable, dict, or None
            The table data.
            Pyarrow tables are not supported by Streamlit's legacy DataFrame serialization
            (i.e. with `config.dataFrameSerialization = "legacy"`).
            To use pyarrow tables, please enable pyarrow by changing the config setting,
            `config.dataFrameSerialization = "arrow"`.

        Example
        -------
        >>> import pandas as pd
        >>> import numpy as np
        >>>
        >>> df = pd.DataFrame(
        ...    np.random.randn(10, 5),
        ...    columns=('col %d' % i for i in range(5)))
        ...
        >>> st.table(df)

        .. output::
           https://doc-table.streamlitapp.com/
           height: 480px

        """
        if _use_arrow():
            return self.dg._arrow_table(data)
        else:
            return self.dg._legacy_table(data)