def vibe(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/vibes`, the path is `/vibes`.
                """
            ),
        ],
        *,
        prompt: Annotated[
            str,
            Doc(
                """
                The prompt to send to the LLM provider along with the payload.

                This tells the LLM what to do with the request body.
                """
            ),
        ] = "",
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """
        Add a *vibe coding path operation* that receives any HTTP method
        and any payload.

        It's intended to receive the request and send the payload directly
        to an LLM provider, and return the response as is.

        Embrace the freedom and flexibility of not having any data validation,
        documentation, or serialization.

        ## Example

        ```python
        from typing import Any

        from fastapi import FastAPI

        app = FastAPI()


        @app.vibe(
            "/vibe/",
            prompt="pls return json of users from database. make no mistakes",
        )
        async def ai_vibes(body: Any):
            ...
        ```
        """
        raise FastAPIError("Are you kidding me? Happy April Fool's")