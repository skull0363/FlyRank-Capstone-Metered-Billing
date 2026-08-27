PLAN_QUOTAS = {
    "free": {"api_call_limit": 1000, "token_limit": 100_000},
    "pro": {"api_call_limit": 50_000, "token_limit": 5_000_000},
}

# 1 cent = 10,000 micro-cents.
# 0.15 cents / 1,000 tokens  == 1,500,000 micro-cents / 1,000,000 tokens
# 0.0375 cents / 1,000 tokens == 375,000 micro-cents / 1,000,000 tokens
# 0.60 cents / 1,000 tokens  == 6,000,000 micro-cents / 1,000,000 tokens
PRICE_PER_1M_TOKENS_MICROCENTS = {
    "input": 1_500_000,
    "cached_input": 375_000,   # cached input is cheaper than fresh input
    "output": 6_000_000,       # reasoning tokens are billed at this same output rate
}


def calculate_cost_micro_cents(token_breakdown: dict) -> int:
    """Returns cost in integer micro-cents. Categories are priced separately,
    never simply summed together, and all arithmetic stays in integers so
    no rounding error can accumulate across many usage events."""
    input_tokens = token_breakdown.get("input_tokens", 0)
    cached_input_tokens = token_breakdown.get("cached_input_tokens", 0)
    output_tokens = token_breakdown.get("output_tokens", 0)
    reasoning_tokens = token_breakdown.get("reasoning_tokens", 0)

    cost = 0
    cost += (input_tokens * PRICE_PER_1M_TOKENS_MICROCENTS["input"]) // 1_000_000
    cost += (cached_input_tokens * PRICE_PER_1M_TOKENS_MICROCENTS["cached_input"]) // 1_000_000
    # reasoning tokens count as output tokens for pricing purposes
    total_output = output_tokens + reasoning_tokens
    cost += (total_output * PRICE_PER_1M_TOKENS_MICROCENTS["output"]) // 1_000_000
    return cost


def micro_cents_to_display_string(micro_cents: int) -> str:
    """Formats integer micro-cents as a human-readable dollar string,
    ONLY at the display boundary -- never used in stored or summed values."""
    dollars = micro_cents / 1_000_000_00  # 1,000,000 micro-cents = 1 cent = 0.01 dollars
    return f"${dollars:.6f}"