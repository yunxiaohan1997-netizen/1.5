"""
Pydantic models for the Autonomous Vehicles Alliance Game API.
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime

class SimulationConfig(BaseModel):
    """Configuration for starting a new simulation."""
    num_rounds: int = Field(ge=1, le=50, description="Number of rounds to play")
    information_mode: Literal["asymmetric", "symmetric"] = Field(
        description="Whether agents see only their own payoffs (asymmetric) or both (symmetric)"
    )
    am_strategy: Literal["cooperative", "competitive", "tit-for-tat", "adaptive", "neutral"] = Field(
        description="Strategy for AM agent"
    )
    mc_strategy: Literal["cooperative", "competitive", "tit-for-tat", "adaptive", "neutral"] = Field(
        description="Strategy for MC agent"
    )

class ReasoningStep(BaseModel):
    """A single step in the agent's reasoning process."""
    step: str = Field(description="Step name/title")
    content: str = Field(description="Step content/reasoning")

class AgentDecision(BaseModel):
    """Decision made by an agent for a single round."""
    investment: int = Field(ge=0, le=25, description="Number of engineers allocated")
    reasoning_steps: List[ReasoningStep] = Field(description="Structured reasoning for frontend display")
    full_reasoning: str = Field(description="Complete GPT-4 response for research logs")

class RoundOutcome(BaseModel):
    """Complete outcome of a single round."""
    round: int
    am_decision: AgentDecision
    mc_decision: AgentDecision
    outcomes: dict = Field(description="Payoff calculations")

class SimulationStartResponse(BaseModel):
    """Response when starting a new simulation."""
    simulation_id: str
    status: str
    config: SimulationConfig

class RoundRequest(BaseModel):
    """Request to run the next round."""
    simulation_id: str

class ChatRequest(BaseModel):
    """Request to chat with an agent."""
    simulation_id: str
    agent: Literal["am", "mc"]
    message: str

class ChatResponse(BaseModel):
    """Response from an agent in chat."""
    agent: str
    response: str
    timestamp: datetime

class ExportData(BaseModel):
    """Complete simulation data for export."""
    simulation_id: str
    timestamp: str
    config: dict
    rounds: List[dict]
    summary: dict
