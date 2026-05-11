# ONLINE FLOW - Complete Turn-by-Turn Gaming

## NEW METHODS TO ADD TO main.py

### 1. Helper: Get opponent ID
```python
def _get_opponent_id(self) -> str:
    """Récupère l'ID de l'adversaire en mode ONLINE"""
    if not (self._current_match_id and self.current_profile):
        return None
    match_info = self.matchmaking.get_match_info(self._current_match_id)
    if not match_info:
        return None
    player1_id = match_info["player1_id"]
    my_id = self.current_profile["id"]
    return match_info["player2_id"] if player1_id == my_id else player1_id
```

### 2. Show Answer Screen (Player CAN click)
```python
def _show_answer_screen(self, answering_color: str, is_second_chance: bool = False):
    """Affiche l'écran de réponse avec BOUTONS ACTIVÉS"""
    gs = self.game_state
    is_ai_turn = bool(self.ai_player and answering_color == "bleu")
    
    chance_text = " (2ème chance)" if is_second_chance else ""
    print(f"📋 Écran de réponse{chance_text}: {answering_color} peut cliquer")
    
    self.answer_screen.load(
        question       = self._current_question,
        answering_color = answering_color,
        manche         = gs.manche,
        game_state     = gs,
        is_second_chance = is_second_chance,
        ai_mode        = is_ai_turn
    )
    self._show(IDX_ANSWER)
    if is_ai_turn:
        self.ai_player.request_answer(self._current_question)
```

### 3. Show Spectator Screen (Player CANNOT click)
```python
def _show_spectator_screen(self, answering_color: str):
    """Affiche l'écran spectateur: BOUTONS GRISÉS + polling"""
    gs = self.game_state
    
    # Get opponent name
    match_info = self.matchmaking.get_match_info(self._current_match_id)
    opponent_nick = match_info.get("player1_nickname") if match_info["player2_id"] == self.current_profile["id"] else match_info.get("player2_nickname")
    
    print(f"⏳ Écran spectateur: En attente de {opponent_nick}...")
    
    # Load with grayed buttons
    self.answer_screen.load(
        question       = self._current_question,
        answering_color = answering_color,
        manche         = gs.manche,
        game_state     = gs,
        is_second_chance = False,
        ai_mode        = False
    )
    self.answer_screen.disable_options()
    
    # Show waiting banner
    self.answer_screen.show_status(f"⏳ En attente de {opponent_nick}...", color="#4488ff")
    self._show(IDX_ANSWER)
    
    # Start polling to detect opponent's answer
    self._poll_for_opponent_answer(gs.manche + 1, answering_color)
```

### 4. Poll opponent answer (Real-time sync)
```python
def _poll_for_opponent_answer(self, round_number: int, answering_color: str):
    """Polling toutes les 300ms pour détecter la réponse de l'adversaire"""
    self._poll_opponent_timer = QTimer(self)
    self._poll_opponent_timer.timeout.connect(
        lambda: self._check_opponent_answered(round_number, answering_color)
    )
    self._poll_opponent_timer.start(300)

def _check_opponent_answered(self, round_number: int, answering_color: str):
    """Vérifie si l'adversaire a répondu"""
    try:
        answers = self.matchmaking.get_round_answers(self._current_match_id, round_number)
        
        # Check if opponent answered
        for answer in answers:
            if answer["player_id"] != self.current_profile["id"]:
                # Opponent answered!
                self._poll_opponent_timer.stop()
                print(f"⚔️ {answering_color} a répondu: {answer['chosen_answer']}")
                self.answer_screen.show_opponent_answer(
                    answer['chosen_answer'],
                    match_info['player1_nickname'] if answer['player_id'] == match_info['player1_id'] else match_info['player2_nickname'],
                    answering_color
                )
                # Auto-advance after showing
                QTimer.singleShot(2000, self._after_opponent_answered)
    except Exception as e:
        print(f"ℹ️ Polling (continue...): {e}")
```

### 5. After opponent answered
```python
def _after_opponent_answered(self):
    """Logique après que l'adversaire a répondu"""
    gs = self.game_state
    # Determine next phase based on opponent's answer
    # This will be called automatically by polling
    pass
```

## MODIFY EXISTING METHODS

### _on_answer_selected()
When answer is selected (player could click):
1. Check if CORRECT
2. If YES → next manche
3. If NO → show 2ème chance OR opponent's turn (phase ANSWER_B)

### _on_buzzed()
Completely rewrite:
1. Register buzz to DB
2. Check who buzzed first
3. If ME → show answer screen (_show_answer_screen)
4. If OPPONENT → show spectator screen (_show_spectator_screen) with polling

## FLOW DIAGRAM

```
PHASE 1: BUZZ (Both see question)
├─ Player1 & Player2 both see question + buzz buttons
└─ Both can buzz (whoever presses Q or P first wins)

PHASE 2: ANSWER_A (Player1's turn)
├─ Player1 screen: 4 buttons ACTIVE (can click)
├─ Player2 screen: 4 buttons GRAYED + "⏳ En attente de Player1..."
└─ Polling every 300ms to detect Player1's answer

PLAYER1 ANSWERS CORRECTLY
├─ Both: See result screen
└─ Next MANCHE (back to BUZZ)

PLAYER1 ANSWERS WRONG  
├─ Player1: "🔁 2ème chance!" with ACTIVE buttons
└─ Player2: "⏳ Player1 essaie 2ème chance..." GRAYED buttons

AFTER 2ème CHANCE (Player1):
├─ If CORRECT → Next MANCHE
└─ If WRONG → PHASE ANSWER_B (Player2's turn)

PHASE 3: ANSWER_B (Player2's turn)
├─ Player2 screen: 4 buttons ACTIVE
├─ Player1 screen: GRAYED + "En attente de Player2..."
└─ Same polling logic

... and repeat ...
```

## NOTES

- use match_state table to sync phase across both clients
- db schema now supports player1_nickname, player2_nickname
- answer_screen needs new method: disable_options()
- need show_opponent_answer() to display opponent's pick
