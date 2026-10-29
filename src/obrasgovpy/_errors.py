"""Exceptions raised by obrasgovpy.

Every error the package raises inherits from :class:`ObrasgovError`, so a
caller can catch the whole family with one ``except``. The subclasses exist so
that a caller can tell a bad query from a bad connection without parsing
messages.
"""

from __future__ import annotations


class ObrasgovError(Exception):
    """Base class for every error this package raises."""


class FilterError(ObrasgovError):
    """A filter that cannot be turned into a query parameter."""


class ResponseError(ObrasgovError):
    """A response the package cannot make sense of."""


class HTTPError(ObrasgovError):
    """A non-success HTTP status.

    Attributes
    ----------
    status:
        The HTTP status code.
    detail:
        The messages the FastAPI error body carried, when it sent any.
    """

    def __init__(self, message: str, status: int, detail: list | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.detail = detail or []
