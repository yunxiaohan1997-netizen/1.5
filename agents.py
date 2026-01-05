"""
AI Agent decision-making logic using OpenAI GPT-4.
This is the core of the simulation - real AI agents making strategic decisions.
"""

import os
import re
import logging
from typing import List, Dict, Optional
from openai import AsyncOpenAI

from strategies import get_strategy_prompt
from models import AgentDecision, ReasoningStep
from payoffs import get_payoff_matrices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def agent_make_decision(
    agent_name: str,
    strategy: str,
    information_mode: str,
    game_history: List[dict],
    current_round: int,
    total_rounds: int,
    my_cumulative: float,
    partner_cumulative: float
) -> AgentDecision:
    """
    Call GPT-4 to make an investment decision for an agent.
    
    This is the core function where real AI reasoning happens.
    
    Args:
        agent_name: "AM" or "MC"
        strategy: Strategy name (cooperative, competitive, etc.)
        information_mode: "asymmetric" or "symmetric"
        game_history: List of previous rounds with decisions and outcomes
        current_round: Current round number (1-indexed)
        total_rounds: Total number of rounds
        my_cumulative: Agent's cumulative payoff so far
        partner_cumulative: Partner's cumulative payoff so far
    
    Returns:
        AgentDecision with investment, reasoning, and full response
    """
    
    # Get payoff matrices
    payoff_matrices = get_payoff_matrices()
    
    # Company name for prompt
    company_name = "Autonomous Motors (AM)" if agent_name == "AM" else "Motherboard Chips (MC)"
    
    # Get strategy system prompt
    system_prompt = get_strategy_prompt(strategy, company_name)
    
    # Build context-specific user prompt
    user_prompt = build_decision_prompt(
        agent_name=agent_name,
        information_mode=information_mode,
        game_history=game_history,
        current_round=current_round,
        total_rounds=total_rounds,
        my_cumulative=my_cumulative,
        partner_cumulative=partner_cumulative,
        payoff_matrices=payoff_matrices
    )
    
    logger.info(f"Agent {agent_name} (strategy: {strategy}) making decision for round {current_round}")
    
    # Call GPT-4
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        full_response = response.choices[0].message.content
        logger.info(f"Agent {agent_name} GPT-4 response received ({len(full_response)} chars)")
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise
    
    # Parse investment decision from response
    investment = extract_investment_from_response(full_response)
    
    # Validate and constrain investment
    if not (0 <= investment <= 25):
        logger.warning(f"Agent {agent_name} returned invalid investment {investment}, constraining to 0-25")
        investment = max(0, min(25, investment))
    
    # Parse reasoning steps for frontend display
    reasoning_steps = parse_reasoning_steps(full_response)
    
    logger.info(f"Agent {agent_name} decided to invest {investment} engineers")
    
    return AgentDecision(
        investment=investment,
        reasoning_steps=reasoning_steps,
        full_reasoning=full_response
    )


def build_decision_prompt(
    agent_name: str,
    information_mode: str,
    game_history: List[dict],
    current_round: int,
    total_rounds: int,
    my_cumulative: float,
    partner_cumulative: float,
    payoff_matrices
) -> str:
    """
    Build the detailed context prompt for GPT-4 decision-making.
    
    This prompt provides all the information the agent needs to make an informed decision.
    """
    
    prompt = f"""You are making an investment decision for Round {current_round} of {total_rounds}.

PAYOFF MATRIX (Your Net Benefit):
This shows YOUR net benefit for each combination of investments.
Rows = Your engineers (0-25), Columns = Partner's engineers (0-25)

"""
    
    # Show agent's own payoff matrix sample
    prompt += payoff_matrices.get_payoff_matrix_sample(agent_name.lower())
    
    # Show partner's matrix if symmetric information
    if information_mode == "symmetric":
        partner_name = "MC" if agent_name == "AM" else "AM"
        prompt += "\n\nPARTNER'S PAYOFF MATRIX (Symmetric Information Mode):\n"
        prompt += "You can see your partner's payoffs, giving you strategic advantage.\n\n"
        prompt += payoff_matrices.get_payoff_matrix_sample(partner_name.lower())
    else:
        prompt += "\n\nINFORMATION MODE: Asymmetric\n"
        prompt += "You do NOT know your partner's exact payoff matrix.\n"
        prompt += "You must infer their incentives from their behavior.\n"
    
    # Show game history
    if game_history:
        prompt += f"\n\nGAME HISTORY ({len(game_history)} rounds completed):\n"
        for h in game_history:
            my_key = f"{agent_name.lower()}_investment"
            partner_key = f"{'mc' if agent_name == 'AM' else 'am'}_investment"
            my_payoff_key = f"{agent_name.lower()}_payoff"
            partner_payoff_key = f"{'mc' if agent_name == 'AM' else 'am'}_payoff"
            
            prompt += f"Round {h['round']}: "
            prompt += f"You invested {h[my_key]}, Partner invested {h[partner_key]} → "
            prompt += f"You earned ${h[my_payoff_key]:.2f}, Partner earned ${h[partner_payoff_key]:.2f}\n"
    else:
        prompt += "\n\nGAME HISTORY: This is Round 1 - no history yet.\n"
        prompt += "This is your opening move. What signal do you want to send?\n"
    
    # Current cumulative scores
    prompt += f"\n\nCUMULATIVE SCORES:"
    prompt += f"\n- Your total payoff: ${my_cumulative:.2f}"
    prompt += f"\n- Partner's total payoff: ${partner_cumulative:.2f}"
    
    if my_cumulative > 0 or partner_cumulative > 0:
        diff = my_cumulative - partner_cumulative
        if diff > 0:
            prompt += f"\n- You are ahead by ${diff:.2f}"
        elif diff < 0:
            prompt += f"\n- Partner is ahead by ${-diff:.2f}"
        else:
            prompt += f"\n- Scores are tied"
    
    # The task
    prompt += f"""

TASK: Decide how many engineers (0-25) to allocate for Round {current_round}.

Provide your analysis following this structure:

1. PATTERN ANALYSIS: What patterns do you observe in partner's behavior?
   - Investment trend (increasing/decreasing/stable)
   - Response to your moves
   - Cooperation level assessment

2. PAYOFF CALCULATIONS: Calculate expected payoffs for 3-4 different scenarios.
   - Show the math: "If I invest X and partner invests Y → my payoff = Z"
   - Consider optimistic, realistic, and pessimistic partner responses

3. STRATEGIC REASONING: Apply game theory principles.
   - What equilibrium are you targeting?
   - What signals are you sending?
   - How does this fit your overall strategy?

4. DECISION: State your investment decision clearly.

5. CONFIDENCE & CONTINGENCY: How confident are you? What could change your mind?

CRITICAL: End your response with a clear statement:
"FINAL DECISION: [number] engineers"

Think step-by-step. Show your strategic reasoning.
"""
    
    return prompt


def extract_investment_from_response(response: str) -> int:
    """
    Parse GPT-4's response to find the investment decision.
    
    Looks for patterns like:
    - "FINAL DECISION: 15 engineers"
    - "I will invest 18 engineers"
    - "Decision: 12"
    
    Args:
        response: GPT-4's full text response
    
    Returns:
        Integer investment (0-25)
    """
    # Pattern 1: "FINAL DECISION: X engineers" or "FINAL DECISION: X"
    match = re.search(r'FINAL DECISION:\s*(\d+)', response, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Pattern 2: "invest X engineers"
    match = re.search(r'invest\s+(\d+)\s+engineers', response, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Pattern 3: "Decision: X" or "My decision: X"
    match = re.search(r'decision:\s*(\d+)', response, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Pattern 4: "allocate X engineers" or "allocating X"
    match = re.search(r'allocat(?:e|ing)\s+(\d+)', response, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Pattern 5: Look for numbers 0-25 near the end of response
    lines = response.strip().split('\n')
    for line in reversed(lines[-10:]):  # Check last 10 lines
        numbers = re.findall(r'\b(\d+)\b', line)
        for num in numbers:
            n = int(num)
            if 0 <= n <= 25:
                logger.warning(f"Used fallback extraction, found {n} near end of response")
                return n
    
    # Ultimate fallback: middle value
    logger.warning("Could not extract investment from response, using fallback value 12")
    return 12


def parse_reasoning_steps(response: str) -> List[ReasoningStep]:
    """
    Parse GPT-4's response into structured reasoning steps for frontend display.
    
    Tries to extract numbered sections from the response.
    Falls back to paragraph splitting if structure not found.
    
    Args:
        response: GPT-4's full text response
    
    Returns:
        List of ReasoningStep objects
    """
    steps = []
    
    # Define section patterns to look for
    sections = {
        "Pattern Analysis": r'1\.\s*PATTERN ANALYSIS[:\s]+(.*?)(?=2\.|$)',
        "Payoff Calculations": r'2\.\s*PAYOFF CALCULATIONS[:\s]+(.*?)(?=3\.|$)',
        "Strategic Reasoning": r'3\.\s*STRATEGIC REASONING[:\s]+(.*?)(?=4\.|$)',
        "Decision": r'4\.\s*DECISION[:\s]+(.*?)(?=5\.|$)',
        "Confidence": r'5\.\s*(?:CONFIDENCE|CONTINGENCY)[:\s]+(.*?)(?=FINAL|$)',
    }
    
    for title, pattern in sections.items():
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Limit content length for frontend display
            if len(content) > 400:
                content = content[:400] + "..."
            steps.append(ReasoningStep(step=title, content=content))
    
    # If structured parsing failed, split by paragraphs
    if not steps:
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip() and len(p.strip()) > 20]
        for i, para in enumerate(paragraphs[:6]):  # Max 6 steps
            # Limit paragraph length
            if len(para) > 400:
                para = para[:400] + "..."
            steps.append(ReasoningStep(
                step=f"Reasoning {i+1}",
                content=para
            ))
    
    # Ensure we have at least one step
    if not steps:
        steps.append(ReasoningStep(
            step="Analysis",
            content=response[:400] + ("..." if len(response) > 400 else "")
        ))
    
    return steps


async def chat_with_agent(
    agent_name: str,
    message: str,
    game_state: dict
) -> str:
    """
    User chats with an agent. Agent responds in character based on game state.
    
    Args:
        agent_name: "AM" or "MC"
        message: User's question
        game_state: Current simulation state
    
    Returns:
        Agent's response string
    """
    
    company_name = "Autonomous Motors (AM)" if agent_name == "AM" else "Motherboard Chips (MC)"
    partner_name = "MC" if agent_name == "AM" else "AM"
    
    # Extract relevant game state
    current_round = game_state.get('current_round', 0)
    history = game_state.get('history', [])
    
    my_key = agent_name.lower()
    partner_key = 'mc' if agent_name == 'AM' else 'am'
    
    my_cumulative = game_state.get(f'{my_key}_cumulative', 0)
    partner_cumulative = game_state.get(f'{partner_key}_cumulative', 0)
    
    # Build complete history context
    history_context = ""
    if history:
        history_context = "Complete game history:\n"
        for round_data in history:
            round_num = round_data.get('round', 0)
            my_inv = round_data.get(f'{my_key}_investment', 'N/A')
            partner_inv = round_data.get(f'{partner_key}_investment', 'N/A')
            my_payoff = round_data.get(f'{my_key}_payoff', 0)
            partner_payoff = round_data.get(f'{partner_key}_payoff', 0)
            history_context += f"Round {round_num}: You invested {my_inv}, Partner invested {partner_inv} | Your payoff: ${my_payoff:.2f}, Partner payoff: ${partner_payoff:.2f}\n"
    else:
        history_context = "No rounds completed yet."
    
    # Get last round data
    my_last_investment = None
    partner_last_investment = None
    if history:
        last_round = history[-1]
        my_last_investment = last_round.get(f'{my_key}_investment')
        partner_last_investment = last_round.get(f'{partner_key}_investment')
    
    # Build chat context with complete history
    system_prompt = f"""You are a senior executive at {company_name} participating in a strategic alliance negotiation for autonomous vehicle development.

CRITICAL: Stay in character. You are NOT an AI assistant. You are a business executive with strategic responsibilities.

{history_context}

Current situation:
- Current round: {current_round}
- Your last investment: {my_last_investment if my_last_investment is not None else 'Not started'} engineers
- Partner's last investment: {partner_last_investment if partner_last_investment is not None else 'Not started'} engineers  
- Your cumulative payoff: ${my_cumulative:.2f}
- Partner's cumulative payoff: ${partner_cumulative:.2f}

When responding:
- Reference SPECIFIC round numbers and investments when asked
- Use business and strategy terminology
- Explain using game theory concepts (Nash equilibrium, dominant strategies, repeated games)
- Show strategic sophistication and deep analysis
- Be direct and professional
- Keep responses under 150 words
- Do NOT break character or mention being an AI
"""
    
    user_prompt = f"""The user asks: "{message}"

Respond as the executive of your company. Reference the current game data where relevant. Explain your strategic thinking concisely.
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=300
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {e}")
        return f"I apologize, but I'm having difficulty responding right now. As the executive at {company_name}, I'm focused on our strategic position in this alliance."
