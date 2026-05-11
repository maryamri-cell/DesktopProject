# Technical Documentation: Ahsan Khota Computer Opponent (AI)

This document explains the architecture and logic behind the **Computer Opponent** system in Ahsan Khota. The system was recently refactored from a Reinforcement Learning (Q-Learning) approach to a **deterministic, rule-based, human-like simulation**.

---

## 1. Core Philosophy
The objective of the AI is to simulate a **credible football fan**, not a perfect machine. The AI makes mistakes, hesitates, and relies on "football culture" rather than reading hidden internal game data.

### Key Principles:
- **No Cheating**: The AI does not read hidden ratings or rarity tiers directly.
- **Human Imperfection**: It misjudges players, fails questions, and panics under pressure.
- **Deterministic**: Given the same match seed, the AI will always make the same decisions.

---

## 2. Architecture Overview

The system is divided into three modular layers:

### A. `ai/profiles.py` (Data Layer)
Defines the characteristics of the three difficulty levels:
- **EASY**: Low accuracy (~40%), high hesitation, slow reactions (~3.5s), high error margin in player evaluation.
- **MEDIUM**: Balanced accuracy (~65%), moderate reactions (~2.5s), decent player evaluation.
- **HARD**: High accuracy (~88%), fast reactions (~1.6s), aggressive buzzing, expert player evaluation.

### B. `ai/agent.py` (Logic Layer)
Houses the `ComputerOpponent` class. It manages:
- **Confidence & Momentum**: Internal state that fluctuates based on success/failure.
- **Player Estimation**: The `_estimate_player_strength` method which simulates "Fame" recognition.
- **Decision Engine**: Determines whether to BUZZ, SKIP, or WAIT.

### C. `ai/integration.py` (Interface Layer)
Houses the `AIPlayer` (QObject). It bridges the logic with the PyQt5 UI using:
- **Non-Linear Timers**: Simulates "thinking time" using Gaussian distributions.
- **Signal Emission**: Emits `buzz_action`, `answer_action`, etc., to the main controller.

---

## 3. Advanced Behavioral Systems

### 3.1 Subjective Player Evaluation (The "Fame" System)
Instead of reading the hidden `__rating`, the AI estimates strength using:
1. **International Reputation**: A visible attribute (1-5 stars) providing a baseline.
2. **Club Prestige**: Players from "Elite" clubs (e.g., Real Madrid, Man City) receive a slight subjective bonus in the AI's mind.
3. **Perceived Overall**: A proxy for the player's general standing.
4. **Gaussian Noise**: A random error factor (larger for Easy, smaller for Hard) that causes the AI to occasionally pick a weaker player over a stronger one.

### 3.2 Human-Like Timing & Hesitation
Timing is not constant. The reaction delay is calculated using:
`Delay = (Base_Reaction * Type_Modifier) + Gauss_Jitter / Momentum`

- **Type Modifiers**: It takes 50% longer to recognize an image (`IMAGE_GUESS`) than to answer a multiple-choice question (`MCQ`).
- **Momentum**: If the AI is on a "winning streak", its confidence increases, reducing its reaction time (it buzzes faster).

### 3.3 Confidence-Driven Strategy
The AI tracks `consecutive_successes` and `consecutive_failures`:
- **Momentum High**: AI becomes aggressive, buzzes earlier, and takes more risks.
- **Momentum Low**: AI becomes "frustrated" or "scared", hesitates longer, and is more likely to use the **SKIP** mechanic.
- **Comeback Logic**: If the AI is losing by a large margin, it automatically enters a "high-risk" mode to attempt a comeback.

---

## 4. Determinism & Seeding
For future online synchronization and debugging, the AI uses a dedicated `random.Random(seed)` instance. 
- The **seed** is generated at the start of the match using: `hash(match_id + difficulty + player_names)`.
- This ensures that two players watching the same AI match (or a replay) see identical behavior.

---

## 5. Integration with Game Flow
The AI acts as a "Virtual Player" through the `AIPlayer` class:
1. **Buzz Phase**: `request_buzz()` starts a thinking timer.
2. **Answer Phase**: `request_answer()` simulates "reading" the suggestions before choosing.
3. **Pick Phase**: `request_pick()` simulates analyzing the two card options.

All AI actions respect the `GameState` phases, ensuring no race conditions or illegal transitions occur during the match.
