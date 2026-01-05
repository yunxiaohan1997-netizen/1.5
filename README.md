# Autonomous Vehicles Alliance Game - AI Simulation Backend

Academic-grade AI agent simulation for strategic management research and MBA education.

## Overview

This is a **real AI simulation system**, not a demo. It uses OpenAI's GPT-4 to create autonomous agents that genuinely reason through strategic decisions in a repeated prisoner's dilemma scenario.

### Key Features

- **Real AI Reasoning**: GPT-4 agents actually think through game theory
- **5 Distinct Strategies**: Cooperative, Competitive, Tit-for-Tat, Adaptive Learning, Neutral
- **Research-Grade Data**: Complete logs of all decisions and reasoning for analysis
- **Information Asymmetry**: Agents can play with or without knowledge of partner's payoffs
- **Interactive Chat**: Ask agents about their strategies mid-game

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API key
- 11_29.xlsx payoff matrix file

### Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. **Place the payoff matrix file**:
```bash
# Ensure 11_29.xlsx is at /mnt/user-data/uploads/11_29.xlsx
# Or update the path in payoffs.py
```

4. **Run the server**:
```bash
python main.py
```

Server will start at `http://localhost:8000`

## API Documentation

### Start Simulation

```bash
POST /api/simulation/start
Content-Type: application/json

{
  "num_rounds": 10,
  "information_mode": "asymmetric",
  "am_strategy": "cooperative",
  "mc_strategy": "competitive"
}
```

**Response**:
```json
{
  "simulation_id": "uuid-string",
  "status": "initialized",
  "config": {...}
}
```

### Run Next Round

```bash
POST /api/simulation/round
Content-Type: application/json

{
  "simulation_id": "uuid-from-start"
}
```

**Response**:
```json
{
  "round": 1,
  "am_decision": {
    "investment": 15,
    "reasoning_steps": [
      {"step": "Pattern Analysis", "content": "..."},
      {"step": "Payoff Calculations", "content": "..."}
    ]
  },
  "mc_decision": {
    "investment": 12,
    "reasoning_steps": [...]
  },
  "outcomes": {
    "am_payoff": 385.0,
    "mc_payoff": 299.0,
    "total_welfare": 684.0,
    "am_cumulative": 385.0,
    "mc_cumulative": 299.0
  }
}
```

### Chat with Agent

```bash
POST /api/chat
Content-Type: application/json

{
  "simulation_id": "uuid",
  "agent": "am",
  "message": "Why did you invest so much?"
}
```

**Response**:
```json
{
  "agent": "am",
  "response": "Given our cooperative strategy and the importance of signaling trust in this alliance, investing 18 engineers demonstrates commitment. This positions us for sustained mutual value creation across the remaining 7 rounds.",
  "timestamp": "2024-12-28T10:30:45.123Z"
}
```

### Export Simulation Data

```bash
GET /api/simulation/{simulation_id}/export
```

Returns complete simulation data including all rounds, reasoning, and summary statistics.

## Strategies Explained

### 1. Cooperative
- Maximizes joint welfare
- Signals trustworthiness
- Maintains high investment if partner reciprocates
- Gradually reduces if exploited repeatedly

### 2. Competitive
- Maximizes own payoff, even at partner's expense
- Seeks to free-ride (low investment while partner invests high)
- Tests partner's willingness to cooperate
- Only cooperates enough to prevent total collapse

### 3. Tit-for-Tat
- Starts cooperative (15 engineers)
- Mirrors partner's last move
- Classic game theory strategy (won Axelrod's tournament)
- "Nice, retaliatory, forgiving, clear"

### 4. Adaptive Learning
- Uses Bayesian reasoning to infer partner type
- Updates beliefs each round
- Optimizes response based on probability-weighted expectations
- Balances exploration (learning) vs exploitation (profit)

### 5. Neutral
- Pure mathematical optimization
- No cooperation/competition bias
- Calculates expected values
- Plays best response to predicted partner move

## Information Modes

### Asymmetric (Realistic)
- Each agent only sees their own payoff matrix
- Must infer partner's incentives from behavior
- Simulates real-world information barriers

### Symmetric (Control)
- Both agents see both payoff matrices
- Tests how transparency affects cooperation
- Useful for research comparisons

## For Research Use

### Data Export Format

The `/export` endpoint returns JSON with:

```json
{
  "simulation_id": "...",
  "config": {
    "information_mode": "asymmetric",
    "am_strategy": "cooperative",
    "mc_strategy": "competitive",
    "num_rounds": 10
  },
  "summary": {
    "total_rounds": 10,
    "am_total_payoff": 4200.50,
    "mc_total_payoff": 3800.25,
    "avg_welfare_per_round": 800.08,
    "cooperation_index": 0.65
  },
  "rounds": [
    {
      "round": 1,
      "am_investment": 15,
      "mc_investment": 12,
      "am_payoff": 385.0,
      "mc_payoff": 299.0,
      "am_reasoning": "Full GPT-4 response...",
      "mc_reasoning": "Full GPT-4 response...",
      "timestamp": "..."
    }
  ]
}
```

### Running Experiments

Example: Test if cooperation emerges more under symmetric vs asymmetric information.

```python
import requests
import json

# Run 20 simulations with cooperative vs competitive
results = []

for i in range(20):
    # Half with asymmetric, half with symmetric
    info_mode = "asymmetric" if i < 10 else "symmetric"
    
    # Start simulation
    response = requests.post("http://localhost:8000/api/simulation/start", json={
        "num_rounds": 10,
        "information_mode": info_mode,
        "am_strategy": "cooperative",
        "mc_strategy": "competitive"
    })
    sim_id = response.json()['simulation_id']
    
    # Run all rounds
    for round in range(10):
        requests.post("http://localhost:8000/api/simulation/round", json={
            "simulation_id": sim_id
        })
    
    # Export data
    data = requests.get(f"http://localhost:8000/api/simulation/{sim_id}/export").json()
    results.append(data)

# Save results
with open('experiment_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Analyze in R, Python, Stata, etc.
```

## Architecture

```
backend/
├── main.py           # FastAPI app, endpoints, state management
├── agents.py         # GPT-4 agent decision logic
├── strategies.py     # 5 strategy prompts (the "brains")
├── payoffs.py        # Excel loading, payoff calculations
├── models.py         # Pydantic data models
├── requirements.txt  # Python dependencies
└── .env.example      # Environment variables template
```

## Quality Standards

This system meets academic research standards:

✅ **Real AI**: GPT-4 actually reasons, not rule-based bots  
✅ **Reproducible**: Same config produces similar patterns  
✅ **Rigorous**: Decisions based on game theory  
✅ **Exportable**: Complete data for statistical analysis  
✅ **Publishable**: Can be used in peer-reviewed research  

## Cost Considerations

- GPT-4 costs ~$0.03-0.06 per round (both agents)
- 10-round simulation: ~$0.30-0.60
- 100 simulations for research: ~$30-60

Set token limits and monitor usage in production.

## Troubleshooting

### "Simulation not found"
- Simulations are stored in-memory
- They're lost on server restart
- Use Redis or database for persistence

### "OpenAI API error"
- Check API key in .env
- Verify you have GPT-4 access
- Check rate limits on your OpenAI account

### Agents making nonsensical decisions
- Review full_reasoning in export data
- Check if prompt context is clear
- Verify payoff matrices loaded correctly

## Frontend Integration

Update the frontend HTML file:

```javascript
// In autonomous-vehicles-alliance-simulation.html
const API_BASE = "http://localhost:8000";
```

All API calls will work as designed.

## License

Academic and research use encouraged. For commercial use, contact authors.

## Citation

If you use this system in published research, please cite:

```
@software{av_alliance_simulation,
  title={Autonomous Vehicles Alliance Game: AI Agent Simulation},
  author={[Your Name]},
  year={2024},
  note={GPT-4-powered strategic management simulation}
}
```

## Support

For issues, questions, or collaboration:
- Review the code comments
- Check API documentation above
- Examine exported data for debugging
- Test with simple scenarios first

---

**Remember**: This is a research instrument, not a toy. Treat it with the rigor it deserves.
