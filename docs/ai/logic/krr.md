---
layout: default
title: KRR
parent: Logic
grand_parent: AI
nav_order: 1
---

# KRR

"KRR" stands for Knowledge Representation and Reasoning. It's focused on how to represent information about the world in a form that a computer system can utilize to solve complex tasks like diagnosing a medical condition, playing a chess game, or navigating through a robot.

Logical agents in KRR refer to agents that employ logic to represent their knowledge base and apply logical reasoning to make decisions. The logic used can vary from simple propositional logic to more complex forms like first-order logic or description logic. Here's a brief overview of how logical agents operate:

1. Knowledge Base (KB): domain−specific content. Knowledge base = set of sentences in a formal language. This is where the agent stores all the information it has about the world, represented in a logical format. The knowledge base includes facts about the environment and the rules that govern its behavior.

2. Inference Engine: domain−independent algorithms. This component of the agent uses the rules and facts stored in the KB to infer new information or make decisions. The inference process could be based on different methods of logical reasoning such as deduction, induction, and abduction.

3. Query Processing: Logical agents often need to respond to queries or solve problems posed by the users or other agents. The inference engine processes these queries by applying logical rules to the knowledge base to derive answers.

KRR systems are particularly useful in domains where the knowledge can be clearly defined using logical constructs, and where deductive reasoning can be applied to derive conclusions from known facts. Examples include expert systems in medicine, automated planning systems, and certain types of AI in games.

example : Wumpus World

PEAS description : PEAS System is used to categorize similar agents together : Performance Measure, Environment, Actuator, Sensor

Performance measure
gold +1000, death -1000
-1 per step, -10 for using the arrow

Environment
Squares adjacent to wumpus are smelly
Squares adjacent to pit are breezy
Glitter iff gold is in the same square
Shooting kills wumpus if you are facing it
Shooting uses up the only arrow
Grabbing picks up gold if in same square
Releasing drops the gold in same square

Actuators 
Left turn, Right turn, Forward, Grab, Release, Shoot

Sensors 
Breeze, Glitter, Smell