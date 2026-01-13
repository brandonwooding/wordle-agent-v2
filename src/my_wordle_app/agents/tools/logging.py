import json
from copy import deepcopy
from typing import Any, Dict, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.models import LlmRequest, LlmResponse


def _safe(x: Any) -> Any:
    try:
        json.dumps(x)
        return x
    except TypeError:
        return repr(x)


def _pretty(d: Dict[str, Any]) -> str:
    return json.dumps({k: _safe(v) for k, v in d.items()}, indent=2, sort_keys=True)


def _diff(prev: Dict[str, Any], cur: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k in sorted(set(prev) | set(cur)):
        if prev.get(k) != cur.get(k):
            out[k] = {"from": _safe(prev.get(k)), "to": _safe(cur.get(k))}
    return out


# ---- Agent lifecycle ----
def before_agent_callback(*, callback_context: CallbackContext, **kwargs):
    print(f"\n=== BEFORE_AGENT agent={callback_context.agent_name} inv={callback_context.invocation_id} ===")
    print(_pretty(callback_context.state.to_dict()))
    return None


def after_agent_callback(*, callback_context: CallbackContext, **kwargs):
    print(f"\n=== AFTER_AGENT agent={callback_context.agent_name} inv={callback_context.invocation_id} ===")
    print(_pretty(callback_context.state.to_dict()))
    return None


# ---- Model lifecycle (LlmAgent) ----
def before_model_callback(*, callback_context: CallbackContext, llm_request: LlmRequest, **kwargs) -> Optional[LlmResponse]:
    print(f"\n=== BEFORE_MODEL agent={callback_context.agent_name} inv={callback_context.invocation_id} ===")
    print("STATE:")
    print(_pretty(callback_context.state.to_dict()))
    return None  # returning LlmResponse would skip the model call :contentReference[oaicite:1]{index=1}


def after_model_callback(*, callback_context: CallbackContext, llm_response: LlmResponse, **kwargs) -> Optional[LlmResponse]:
    print(f"\n=== AFTER_MODEL agent={callback_context.agent_name} inv={callback_context.invocation_id} ===")
    return None


# ---- Tool lifecycle ----
def before_tool_callback(*, tool, tool_args: Dict[str, Any], tool_context: ToolContext, **kwargs) -> Optional[dict]:
    prev = deepcopy(tool_context.state.to_dict())
    tool_context.state["temp:_state_prev"] = prev  # temp: is invocation-scoped :contentReference[oaicite:2]{index=2}

    print(f"\n=== BEFORE_TOOL tool={getattr(tool, 'name', lambda: type(tool).__name__)()} ===")
    print("ARGS:", _pretty(tool_args))
    print("STATE:")
    print(_pretty(prev))
    return None  # returning dict would short-circuit the tool call :contentReference[oaicite:3]{index=3}


def after_tool_callback(*, tool, tool_args: Dict[str, Any], tool_context: ToolContext, result: dict, **kwargs) -> Optional[dict]:
    cur = tool_context.state.to_dict()
    prev = tool_context.state.get("temp:_state_prev", {})
    d = _diff(prev if isinstance(prev, dict) else {}, cur)

    print(f"\n=== AFTER_TOOL tool={getattr(tool, 'name', lambda: type(tool).__name__)()} ===")
    print("RESULT:", _pretty(result))
    print("STATE_DIFF:", _pretty(d))
    return None  # return dict here to replace tool result :contentReference[oaicite:4]{index=4}
