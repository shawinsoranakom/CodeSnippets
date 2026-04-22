def column_gap(gap):
            if type(gap) == str:
                gap_size = gap.lower()
                valid_sizes = ["small", "medium", "large"]

                if gap_size in valid_sizes:
                    return gap_size

            raise StreamlitAPIException(
                'The gap argument to st.columns must be "small", "medium", or "large". \n'
                f"The argument passed was {gap}."
            )