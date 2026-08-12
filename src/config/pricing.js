//prices are stored in cents (units of $0.000001)
export const PLAN_LIMITS = {
    FREE: {apiCalls:1000, aiTokens: 10000},
    PRO: {apiCalls: 10000, aiTokens:10000000}
};

export const TOKEN_PRICING = {
    INPUT_MICRO_CENTS: 15, //$1.50 per 1M tokens
    CACHED_INPUT_MICRO_CENTS: 3, //$0.30 per 1M tokens
    OUTPUT_MICRO_CENTS: 60, //$6.00 per 1M tokens
    REASONING_MICRO_CENTS: 60 //Bulled same as output tokens

};

export function calculateAiCost({ inputTokens = 0, cachedInputTokens = 0, outputTokens = 0, reasoningTokens = 0}){
    const effectiveOutput = outputTokens + reasoningTokens;
    const totalCostMicroCents = 
        (inputTokens * TOKEN_PRICING.INPUT_MICRO_CENTS)+
        (cachedInputTokens * TOKEN_PRICING.CACHED_INPUT_MICRO_CENTS)+
        (effectiveOutput * TOKEN_PRICING.OUTPUT_MICRO_CENTS);
    return totalCostMicroCents / 1000000;
}