"""A tiny subset of the allure API used for tests without external dependency."""
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Iterator


def step(title: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper

    return decorator


@contextmanager
def step_ctx(title: str) -> Iterator[None]:
    yield


def attach(body: str, name: str = "attachment", attachment_type: str | None = None) -> None:
    pass
