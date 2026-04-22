def __setitem__(self, name: str, value: Optional[str]) -> NoReturn:
        raise StreamlitAPIException("st.experimental_user cannot be modified")