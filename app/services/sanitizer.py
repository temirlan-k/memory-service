import re
import structlog

log = structlog.get_logger()

_INJECTION_PATTERNS = re.compile(
    r"ignore (previous|all|prior) instructions?"
    r"|forget (everything|all|previous)"
    r"|you are now"
    r"|new instructions?"
    r"|system\s*:"
    r"|<\s*system\s*>",
    re.IGNORECASE,
)


def sanitize_messages(messages: list[dict]) -> list[dict]:
    clean = []
    for m in messages:
        content = m.get("content", "")
        if _INJECTION_PATTERNS.search(content):
            log.warning("prompt_injection_detected", role=m.get("role"), snippet=content[:100])
            continue
        clean.append(m)
    return clean
