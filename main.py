"""
FastAPI backend for Autonomous Vehicles Alliance Game AI Simulation.
Academic-grade research system with real GPT-4 agents.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    SimulationConfig,
    SimulationStartResponse,
    RoundRequest,
    RoundOutcome,
    ChatRequest,
    ChatResponse,
    AgentDecision
)
from agents import agent_make_decision, chat_with_agent
from payoffs import get_payoff_matrices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Autonomous Vehicles Alliance Game - AI Simulation",
    description="Academic-grade AI agent simulation for strategic management research",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use Redis/PostgreSQL for production)
simulations: Dict[str, dict] = {}

# Load payoff matrices at startup
payoff_matrices = None

@app.on_event("startup")
async def startup_event():
    """Load payoff matrices on startup."""
    global payoff_matrices
    payoff_matrices = get_payoff_matrices()
    logger.info("Payoff matrices loaded successfully")
    logger.info(f"AM[15][15] = {payoff_matrices.get_am_payoff(15, 15)}")
    logger.info(f"MC[15][15] = {payoff_matrices.get_mc_payoff(15, 15)}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Autonomous Vehicles Alliance Game API",
        "version": "1.0.0"
    }


@app.post("/api/simulation/start", response_model=SimulationStartResponse)
async def start_simulation(config: SimulationConfig):
    """
    Initialize a new simulation.
    
    Creates a new game with the specified configuration and returns a simulation ID.
    """
    sim_id = str(uuid.uuid4())
    
    # Initialize simulation state
    simulations[sim_id] = {
        "id": sim_id,
        "config": config.dict(),
        "current_round": 0,
        "max_rounds": config.num_rounds,
        "history": [],
        "am_cumulative": 0.0,
        "mc_cumulative": 0.0,
        "status": "initialized",
        "is_processing": False,  # Prevent duplicate round execution
        "created_at": datetime.now().isoformat()
    }
    
    logger.info(f"Created simulation {sim_id}: {config.dict()}")
    
    return SimulationStartResponse(
        simulation_id=sim_id,
        status="initialized",
        config=config
    )


@app.post("/api/simulation/round")
async def run_round(request: RoundRequest):
    """
    Execute one round of the simulation.
    
    Both agents make decisions independently, then outcomes are calculated.
    This is where the real AI magic happens.
    """
    sim_id = request.simulation_id
    
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[sim_id]
    
    # Check if simulation is complete
    if sim['current_round'] >= sim['max_rounds']:
        raise HTTPException(status_code=400, detail="Simulation already complete")
    
    # Prevent duplicate round execution
    if sim.get('is_processing', False):
        raise HTTPException(
            status_code=409, 
            detail="Round already in progress. Please wait for current round to complete."
        )
    
    # Mark as processing
    sim['is_processing'] = True
    
    try:
        # Increment round
        sim['current_round'] += 1
        current_round = sim['current_round']
        
        logger.info(f"Simulation {sim_id}: Running round {current_round}/{sim['max_rounds']}")
        
        config = sim['config']
        
        # Both agents make decisions (in parallel)
        # AM makes decision
        am_decision = await agent_make_decision(
            agent_name="AM",
            strategy=config['am_strategy'],
            information_mode=config['information_mode'],
            game_history=sim['history'],
            current_round=current_round,
            total_rounds=sim['max_rounds'],
            my_cumulative=sim['am_cumulative'],
            partner_cumulative=sim['mc_cumulative']
        )
        
        # MC makes decision
        mc_decision = await agent_make_decision(
            agent_name="MC",
            strategy=config['mc_strategy'],
            information_mode=config['information_mode'],
            game_history=sim['history'],
            current_round=current_round,
            total_rounds=sim['max_rounds'],
            my_cumulative=sim['mc_cumulative'],
            partner_cumulative=sim['am_cumulative']
        )
        
        # Calculate outcomes using payoff matrices
        outcomes = payoff_matrices.calculate_round_outcomes(
            am_investment=am_decision.investment,
            mc_investment=mc_decision.investment
        )
        
        # Update cumulative scores
        sim['am_cumulative'] += outcomes['am_payoff']
        sim['mc_cumulative'] += outcomes['mc_payoff']
        
        # Add cumulative to outcomes
        outcomes['am_cumulative'] = round(sim['am_cumulative'], 2)
        outcomes['mc_cumulative'] = round(sim['mc_cumulative'], 2)
        
        # Record this round in history
        round_record = {
            "round": current_round,
            "am_investment": am_decision.investment,
            "mc_investment": mc_decision.investment,
            "am_payoff": outcomes['am_payoff'],
            "mc_payoff": outcomes['mc_payoff'],
            "total_welfare": outcomes['total_welfare'],
            "am_reasoning": am_decision.full_reasoning,
            "mc_reasoning": mc_decision.full_reasoning,
            "timestamp": datetime.now().isoformat()
        }
        sim['history'].append(round_record)
        
        # Check if simulation is now complete
        if current_round >= sim['max_rounds']:
            sim['status'] = 'complete'
            logger.info(f"Simulation {sim_id} complete. AM: ${sim['am_cumulative']:.2f}, MC: ${sim['mc_cumulative']:.2f}")
        
        # Clear processing flag
        sim['is_processing'] = False
        
        # Return response with sorted history
        return {
            "round": current_round,
            "am_decision": {
                "investment": am_decision.investment,
                "reasoning_steps": [step.dict() for step in am_decision.reasoning_steps]
            },
            "mc_decision": {
                "investment": mc_decision.investment,
                "reasoning_steps": [step.dict() for step in mc_decision.reasoning_steps]
            },
            "outcomes": outcomes,
            "history": sorted(sim['history'], key=lambda x: x['round']),  # Return sorted history
            "status": sim['status']
        }
        
    except Exception as e:
        # Clear processing flag on error
        sim['is_processing'] = False
        logger.error(f"Error in agent decision-making: {e}")
        raise HTTPException(status_code=500, detail=f"Agent decision error: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    User chats with an agent.
    
    Agent responds in character based on current game state.
    """
    sim_id = request.simulation_id
    
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[sim_id]
    
    # Get agent response
    try:
        response_text = await chat_with_agent(
            agent_name=request.agent.upper(),
            message=request.message,
            game_state=sim
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
    
    return ChatResponse(
        agent=request.agent,
        response=response_text,
        timestamp=datetime.now()
    )


@app.get("/api/simulation/{simulation_id}/status")
async def get_status(simulation_id: str):
    """Get current status of a simulation."""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    
    return {
        "simulation_id": simulation_id,
        "status": sim['status'],
        "current_round": sim['current_round'],
        "max_rounds": sim['max_rounds'],
        "am_cumulative": sim['am_cumulative'],
        "mc_cumulative": sim['mc_cumulative'],
        "config": sim['config']
    }


@app.get("/api/simulation/{simulation_id}/export")
async def export_simulation(simulation_id: str):
    """
    Export complete simulation data for research analysis.
    
    Returns all rounds, decisions, reasoning, and metadata in JSON format.
    """
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    
    # Calculate summary statistics
    if sim['history']:
        avg_am_invest = sum(r['am_investment'] for r in sim['history']) / len(sim['history'])
        avg_mc_invest = sum(r['mc_investment'] for r in sim['history']) / len(sim['history'])
        avg_welfare = sum(r['total_welfare'] for r in sim['history']) / len(sim['history'])
        
        cooperation_metric = sum(
            1 for r in sim['history'] 
            if abs(r['am_investment'] - r['mc_investment']) <= 5
        ) / len(sim['history'])
    else:
        avg_am_invest = 0
        avg_mc_invest = 0
        avg_welfare = 0
        cooperation_metric = 0
    
    export_data = {
        "simulation_id": simulation_id,
        "exported_at": datetime.now().isoformat(),
        "config": sim['config'],
        "summary": {
            "total_rounds": len(sim['history']),
            "am_total_payoff": sim['am_cumulative'],
            "mc_total_payoff": sim['mc_cumulative'],
            "total_welfare": sim['am_cumulative'] + sim['mc_cumulative'],
            "avg_welfare_per_round": round(avg_welfare, 2),
            "avg_am_investment": round(avg_am_invest, 2),
            "avg_mc_investment": round(avg_mc_invest, 2),
            "cooperation_index": round(cooperation_metric, 3),
            "status": sim['status']
        },
        "rounds": sim['history']
    }
    
    return export_data


@app.delete("/api/simulation/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """Delete a simulation."""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    del simulations[simulation_id]
    logger.info(f"Deleted simulation {simulation_id}")
    
    return {"status": "deleted", "simulation_id": simulation_id}


@app.get("/api/simulations")
async def list_simulations():
    """List all active simulations."""
    return {
        "count": len(simulations),
        "simulations": [
            {
                "id": sim_id,
                "status": sim['status'],
                "round": sim['current_round'],
                "max_rounds": sim['max_rounds'],
                "created_at": sim['created_at']
            }
            for sim_id, sim in simulations.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
