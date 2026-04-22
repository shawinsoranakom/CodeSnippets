def exists(cls) -> bool:
        """True if the singleton Runtime instance has been created.

        When a Streamlit app is running in "raw mode" - that is, when the
        app is run via `python app.py` instead of `streamlit run app.py` -
        the Runtime will not exist, and various Streamlit functions need
        to adapt.
        """
        return cls._instance is not None