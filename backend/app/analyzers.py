import tiktoken
from radon.complexity import cc_visit

def calculate_complexity(code: str) -> int:
    """Calculates Cyclomatic Complexity using Radon (Python-only fallback)."""
    try:
        blocks = cc_visit(code)
        return sum(block.complexity for block in blocks)
    except Exception:
        return 0 

def calculate_tokens(text: str) -> int:
    """Calculates token count using tiktoken (cl100k_base)."""
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return 0