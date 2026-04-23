def __init__(
        self,
        grant_type: Annotated[
            str,
            Form(pattern="^password$"),
            Doc(
                """
                The OAuth2 spec says it is required and MUST be the fixed string
                "password". This dependency is strict about it. If you want to be
                permissive, use instead the `OAuth2PasswordRequestForm` dependency
                class.

                Read more about it in the
                [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
                """
            ),
        ],
        username: Annotated[
            str,
            Form(),
            Doc(
                """
                `username` string. The OAuth2 spec requires the exact field name
                `username`.

                Read more about it in the
                [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
                """
            ),
        ],
        password: Annotated[
            str,
            Form(),
            Doc(
                """
                `password` string. The OAuth2 spec requires the exact field name
                `password`.

                Read more about it in the
                [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
                """
            ),
        ],
        scope: Annotated[
            str,
            Form(),
            Doc(
                """
                A single string with actually several scopes separated by spaces. Each
                scope is also a string.

                For example, a single string with:

                ```python
                "items:read items:write users:read profile openid"
                ````

                would represent the scopes:

                * `items:read`
                * `items:write`
                * `users:read`
                * `profile`
                * `openid`

                Read more about it in the
                [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
                """
            ),
        ] = "",
        client_id: Annotated[
            str | None,
            Form(),
            Doc(
                """
                If there's a `client_id`, it can be sent as part of the form fields.
                But the OAuth2 specification recommends sending the `client_id` and
                `client_secret` (if any) using HTTP Basic auth.
                """
            ),
        ] = None,
        client_secret: Annotated[
            str | None,
            Form(),
            Doc(
                """
                If there's a `client_secret` (and a `client_id`), they can be sent
                as part of the form fields. But the OAuth2 specification recommends
                sending the `client_id` and `client_secret` (if any) using HTTP Basic
                auth.
                """
            ),
        ] = None,
    ):
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )