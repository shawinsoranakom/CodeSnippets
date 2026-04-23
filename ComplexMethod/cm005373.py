async def stream_output(
        self, stream: Awaitable[AsyncIterator[ChatCompletionStreamOutput]]
    ) -> tuple[str, str | Any | None]:
        self._console.print(f"[bold blue]<{self.model_id}>:")
        with Live(console=self._console, refresh_per_second=4) as live:
            text = ""
            completion_tokens = 0
            start_time = time.time()
            finish_reason: str | None = None
            async for token in await stream:
                outputs = token.choices[0].delta.content
                finish_reason = getattr(token.choices[0], "finish_reason", finish_reason)

                usage = getattr(token, "usage", None)
                if usage is not None:
                    completion_tokens = getattr(usage, "completion_tokens", completion_tokens)

                if not outputs:
                    continue

                # Escapes single words encased in <>, e.g. <think> -> \<think\>, for proper rendering in Markdown.
                # It only escapes single words that may have `_`, optionally following a `/` (e.g. </think>)
                outputs = re.sub(r"<(/*)(\w*)>", r"\<\1\2\>", outputs)

                text += outputs
                # Render the accumulated text as Markdown
                # NOTE: this is a workaround for the rendering "unstandard markdown"
                #  in rich. The chatbots output treat "\n" as a new line for
                #  better compatibility with real-world text. However, rendering
                #  in markdown would break the format. It is because standard markdown
                #  treat a single "\n" in normal text as a space.
                #  Our workaround is adding two spaces at the end of each line.
                #  This is not a perfect solution, as it would
                #  introduce trailing spaces (only) in code block, but it works well
                #  especially for console output, because in general the console does not
                #  care about trailing spaces.

                lines = []
                for line in text.splitlines():
                    lines.append(line)
                    if line.startswith("```"):
                        # Code block marker - do not add trailing spaces, as it would
                        #  break the syntax highlighting
                        lines.append("\n")
                    else:
                        lines.append("  \n")

                markdown = Markdown("".join(lines).strip(), code_theme="github-dark")

                # Update the Live console output
                live.update(markdown, refresh=True)

        elapsed = time.time() - start_time
        if elapsed > 0 and completion_tokens > 0:
            tok_per_sec = completion_tokens / elapsed
            self._console.print()
            self._console.print(f"[dim]{completion_tokens} tokens in {elapsed:.1f}s ({tok_per_sec:.1f} tok/s)[/dim]")
        self._console.print()

        return text, finish_reason