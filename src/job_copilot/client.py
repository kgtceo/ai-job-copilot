"""A thin, testable wrapper over the Anthropic SDK that returns *validated*
Pydantic objects.

The pattern (forced tool use for structured output):
  1. Turn a Pydantic model into a JSON-schema tool.
  2. Force the model to call that tool (`tool_choice`), so it can only answer as
     structured data.
  3. Validate the tool input against the model. If it fails, feed the validation
     error back and retry a bounded number of times — the model self-corrects.

This is the single most reusable piece of applied-LLM plumbing: every step in the
pipeline goes through `structured(...)` and gets back a typed object or raises.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel, ValidationError

from .config import Settings

if TYPE_CHECKING:
    from anthropic import Anthropic

T = TypeVar("T", bound=BaseModel)


class StructuredCallError(RuntimeError):
    """Raised when the model cannot produce schema-valid output within the retry budget."""


class CopilotClient:
    def __init__(self, settings: Settings, anthropic: "Anthropic | None" = None) -> None:
        self._settings = settings
        # Injectable so tests can pass a fake and never hit the network. The SDK is
        # imported lazily so the package (and its offline tests) don't require it.
        if anthropic is None:
            from anthropic import Anthropic

            anthropic = Anthropic(api_key=settings.api_key)
        self._client = anthropic

    def structured(
        self,
        *,
        schema: type[T],
        system: str,
        user: str,
        model: str | None = None,
    ) -> T:
        """Call Claude and return an instance of `schema`, or raise StructuredCallError."""
        tool_name = _tool_name(schema)
        tool = {
            "name": tool_name,
            "description": f"Return the result as a {schema.__name__}.",
            "input_schema": schema.model_json_schema(),
        }

        messages: list[dict] = [{"role": "user", "content": user}]
        last_error: Exception | None = None

        for _attempt in range(self._settings.max_schema_retries + 1):
            response = self._client.messages.create(
                model=model or self._settings.workhorse_model,
                max_tokens=self._settings.max_tokens,
                system=system,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
                messages=messages,
            )
            tool_use = _first_tool_use(response, tool_name)
            if tool_use is None:
                last_error = StructuredCallError("model did not call the output tool")
                continue
            try:
                return schema.model_validate(tool_use.input)
            except ValidationError as exc:
                last_error = exc
                # Hand the exact validation error back so the model can fix itself.
                messages.append({"role": "assistant", "content": response.content})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "That tool input failed validation:\n"
                            f"{exc}\n"
                            "Call the tool again with corrected, schema-valid input."
                        ),
                    }
                )

        raise StructuredCallError(
            f"Could not get schema-valid {schema.__name__} after "
            f"{self._settings.max_schema_retries + 1} attempts: {last_error}"
        )


def _tool_name(schema: type[BaseModel]) -> str:
    # Anthropic tool names must match ^[a-zA-Z0-9_-]{1,64}$.
    return f"emit_{schema.__name__.lower()}"


def _first_tool_use(response, tool_name: str):
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
            return block
    return None
