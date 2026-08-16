PLAN_QUOTAS = {
    "free": {"api_call_limit": 1000, "token_limit": 100_000},
    "pro":  {"api_call_limit": 50_000, "token_limit": 5_000_000},
}

# prices in cents per 1,000 tokens — pin these, cover with tests
PRICE_PER_1K = {
    "input": 0.15,
    "cached_input": 0.0375,   # cached input is cheaper than fresh input
    "output": 0.60,           # reasoning tokens are billed at this same output rate
}

def calculate_cost(token_breakdown: dict) -> float:
    """Returns cost in cents. Categories are priced separately, never simply summed."""
    input_tokens = token_breakdown.get("input_tokens", 0)
    cached_input_tokens = token_breakdown.get("cached_input_tokens", 0)
    output_tokens = token_breakdown.get("output_tokens", 0)
    reasoning_tokens = token_breakdown.get("reasoning_tokens", 0)

    cost = 0.0
    cost += (input_tokens / 1000) * PRICE_PER_1K["input"]
    cost += (cached_input_tokens / 1000) * PRICE_PER_1K["cached_input"]
    # reasoning tokens count as output tokens for pricing purposes
    total_output = output_tokens + reasoning_tokens
    cost += (total_output / 1000) * PRICE_PER_1K["output"]
    return round(cost, 4)