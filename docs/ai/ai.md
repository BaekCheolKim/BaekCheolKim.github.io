---
layout: default
title: AI
nav_order: 2.9
has_children: true
permalink: /docs/ai
---

# Ai

goal : designing rational agents

• Agents and environments : f : P􀀀 → A
• Rationality : Rational ≠ omniscient, Rational ≠ clairvoyant
• PEAS (Performance measure, Environment, Actuators, Sensors)
• Environment types : Observable? Deterministic? Episodic? Static? Discrete? Single-agent? etc.
• Agent types : simple reflex agents, reflex agents with state, goal-based agents, utility-based agents, Learning agents(Exploration vs Exploitation)

# solution stradgity outline

• Problem formulation
• Tree search algorithm
• Uninformed search strategies
• Informed search strategies

# example
Goal-Based Agents : Solving Problems by Searching
• Form of goal-based agent that formulates the problem of reaching a goal in its
environment, searches for a sequence of actions solving the problem, and
executes it.
• Assumptions about the task environment:
– fully observable
– deterministic
– static
– single agent
• Offline (or open-loop) problem solving is suitable under those assumptions;
the entire sequence solution can be executed “eyes closed.”

# Formulate problem
– initial state
e.g., “at Arad”
– successor function : S(x) = set of action–state pairs
e.g., S(Arad) = {<Arad→Zerind,Zerind>,<...,...>,<...,...>}
- goal test : explicit or implicit
e.g., if x = “at Bucharest
e.g., if HasAirport(x) is True”
– path cost : additive
– e.g., sum of distances, number of actions executed, etc.