def prepare_for_tokenization(
        self, text: str, is_split_into_words: bool = False, normalize: bool | None = None, **kwargs
    ) -> tuple[str, dict[str, Any]]:
        """
        Performs any necessary transformations before tokenization.

        This method should pop the arguments from kwargs and return the remaining `kwargs` as well. We test the
        `kwargs` at the end of the encoding process to be sure all the arguments have been used.

        Args:
            text (`str`):
                The text to prepare.
            is_split_into_words (`bool`, *optional*, defaults to `False`):
                Whether or not the input is already pre-tokenized (e.g., split into words). If set to `True`, the
                tokenizer assumes the input is already split into words (for instance, by splitting it on whitespace)
                which it will tokenize.
            normalize (`bool`, *optional*, defaults to `None`):
                Whether or not to apply punctuation and casing normalization to the text inputs. Typically, VITS is
                trained on lower-cased and un-punctuated text. Hence, normalization is used to ensure that the input
                text consists only of lower-case characters.
            kwargs (`dict[str, Any]`, *optional*):
                Keyword arguments to use for the tokenization.

        Returns:
            `tuple[str, dict[str, Any]]`: The prepared text and the unused kwargs.
        """
        normalize = normalize if normalize is not None else self.normalize

        if normalize:
            # normalise for casing
            text = self.normalize_text(text)

        filtered_text = self._preprocess_char(text)

        if has_non_roman_characters(filtered_text) and self.is_uroman:
            if not is_uroman_available():
                logger.warning(
                    "Text to the tokenizer contains non-Roman characters. To apply the `uroman` pre-processing "
                    "step automatically, ensure the `uroman` Romanizer is installed with: `pip install uroman` "
                    "Note `uroman` requires python version >= 3.10"
                    "Otherwise, apply the Romanizer manually as per the instructions: https://github.com/isi-nlp/uroman"
                )
            else:
                uroman = ur.Uroman()
                filtered_text = uroman.romanize_string(filtered_text)

        if self.phonemize:
            if not is_phonemizer_available():
                raise ImportError("Please install the `phonemizer` Python package to use this tokenizer.")

            filtered_text = phonemizer.phonemize(
                filtered_text,
                language="en-us",
                backend="espeak",
                strip=True,
                preserve_punctuation=True,
                with_stress=True,
            )
            filtered_text = re.sub(r"\s+", " ", filtered_text)
        elif normalize:
            # strip any chars outside of the vocab (punctuation)
            filtered_text = "".join(list(filter(lambda char: char in self.encoder, filtered_text))).strip()

        return filtered_text, kwargs