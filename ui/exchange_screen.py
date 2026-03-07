# ============================================================
# ui/exchange_screen.py — Phase d'échange (cartons rouges)
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame, QScrollArea,
                              QGridLayout)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer
from PyQt5.QtGui     import QColor
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config  import (COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU,
                     COLOR_GRAY, COLOR_CARD_BG)
from ui.widgets import SeparatorLine


class MiniPlayerCard(QPushButton):
    """
    Mini carte joueur sélectionnable pour l'échange.
    Affiche nom + club + position (pas le rating).
    """
    toggled_card = pyqtSignal(object, bool)   # (player, selected)

    def __init__(self, player, selectable: bool = False,
                 border_color: str = "#333333", parent=None):
        super().__init__(parent)
        self.player     = player
        self.selectable = selectable
        self._selected  = False
        self._border    = border_color
        self._build(border_color)
        if selectable:
            self.clicked.connect(self._toggle)

    def _build(self, border):
        self.setFixedSize(170, 80)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #181818;
                border: 2px solid {border};
                border-radius: 12px;
                color: white;
                text-align: left;
                padding: 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #222222;
                border-color: {'#888888' if not self._selected else border};
            }}
        """)
        # Texte interne
        lines = (
            f"<b style='font-size:13px'>{self.player.name}</b><br>"
            f"<span style='color:{COLOR_GRAY};font-size:10px'>"
            f"{self.player.club}<br>{self.player.position} • {self.player.age} ans</span>"
        )
        self.setText("")
        # Utiliser un QLabel interne pour rich text
        lbl = QLabel(lines, self)
        lbl.setStyleSheet("background:transparent; border:none; padding:8px;")
        lbl.setWordWrap(True)
        lbl.setGeometry(0, 0, 170, 80)
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _toggle(self):
        if not self.selectable:
            return
        self._selected = not self._selected
        color = COLOR_GREEN if self._selected else self._border
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#0d2a0d' if self._selected else '#181818'};
                border: 2px solid {color};
                border-radius: 12px;
                color: white;
                text-align: left;
                padding: 10px;
                font-size: 12px;
            }}
        """)
        self.toggled_card.emit(self.player, self._selected)

    def reset_selection(self):
        self._selected = False
        self._build(self._border)

    @property
    def is_selected(self):
        return self._selected


class ExchangeScreen(QWidget):
    """
    Phase d'échange après les 11 manches :
    - Affiche les équipes des 2 côtés
    - L'adversaire sélectionne N joueurs à prendre
    - L'équipe pénalisée sélectionne N joueurs à donner en retour
    - Les ratings restent CACHÉS
    - Émet exchanges_done quand terminé
    """

    exchanges_done = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._game_state      = None
        self._pending_team    = None   # équipe avec rouges à traiter
        self._exchanges_left  = 0
        self._phase_take      = True   # True = adversaire prend, False = pénalisé donne
        self._selected_take   = []
        self._selected_give   = []
        self._cards_take      = []
        self._cards_give      = []
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 20)
        root.setSpacing(16)

        # Titre
        title = QLabel("🔄  PHASE D'ÉCHANGE")
        title.setStyleSheet(
            f"color: {COLOR_ROUGE}; font-size: 24px; font-weight: 900; "
            "background: transparent; letter-spacing: 3px;"
        )
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("Les cartons rouges déclenchent des échanges de joueurs — ratings toujours cachés !")
        subtitle.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 12px; background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        root.addWidget(subtitle)

        sep = SeparatorLine()
        root.addWidget(sep)

        # Bannière instruction courante
        self.instruction_lbl = QLabel("")
        self.instruction_lbl.setFixedHeight(48)
        self.instruction_lbl.setStyleSheet(f"""
            background-color: #1a1a1a;
            color: white;
            font-size: 15px;
            font-weight: bold;
            border: 2px solid #333333;
            border-radius: 12px;
        """)
        self.instruction_lbl.setAlignment(Qt.AlignCenter)
        self.instruction_lbl.setWordWrap(True)
        root.addWidget(self.instruction_lbl)

        # Compteur sélection
        self.counter_lbl = QLabel("Sélection : 0 / 1")
        self.counter_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-size: 14px; font-weight: bold; "
            "background: transparent;"
        )
        self.counter_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.counter_lbl)

        # Zone des 2 équipes
        teams_row = QHBoxLayout()
        teams_row.setSpacing(30)

        # Équipe rouge (zone de sélection gauche)
        left_col = QVBoxLayout()
        self.left_title = QLabel("🔴  Équipe Rouge")
        self.left_title.setStyleSheet(
            f"color: {COLOR_ROUGE}; font-size: 16px; font-weight: 900; "
            "background: transparent;"
        )
        self.left_title.setAlignment(Qt.AlignCenter)
        left_col.addWidget(self.left_title)

        self.left_grid = QWidget()
        self.left_grid_lay = QGridLayout(self.left_grid)
        self.left_grid_lay.setSpacing(10)
        self.left_grid_lay.setContentsMargins(0, 0, 0, 0)
        left_col.addWidget(self.left_grid)
        left_col.addStretch()
        teams_row.addLayout(left_col)

        # Flèches échange
        arrow_col = QVBoxLayout()
        arrow_col.setAlignment(Qt.AlignCenter)
        self.arrow_lbl = QLabel("⇄")
        self.arrow_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-size: 40px; background: transparent;"
        )
        self.arrow_lbl.setAlignment(Qt.AlignCenter)
        arrow_col.addWidget(self.arrow_lbl)
        teams_row.addLayout(arrow_col)

        # Équipe bleue (zone de sélection droite)
        right_col = QVBoxLayout()
        self.right_title = QLabel("🔵  Équipe Bleue")
        self.right_title.setStyleSheet(
            f"color: {COLOR_BLEU}; font-size: 16px; font-weight: 900; "
            "background: transparent;"
        )
        self.right_title.setAlignment(Qt.AlignCenter)
        right_col.addWidget(self.right_title)

        self.right_grid = QWidget()
        self.right_grid_lay = QGridLayout(self.right_grid)
        self.right_grid_lay.setSpacing(10)
        self.right_grid_lay.setContentsMargins(0, 0, 0, 0)
        right_col.addWidget(self.right_grid)
        right_col.addStretch()
        teams_row.addLayout(right_col)

        root.addLayout(teams_row)
        root.addStretch()

        # Bouton confirmer
        self.confirm_btn = QPushButton("✅   Confirmer la sélection")
        self.confirm_btn.setFixedHeight(52)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00b844, stop:1 {COLOR_GREEN});
                color: black;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: #33dd77; }}
            QPushButton:pressed {{ background: #009938; }}
            QPushButton:disabled {{
                background: #1a1a1a;
                color: #444444;
            }}
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        root.addWidget(self.confirm_btn)

    # ── API Publique ──────────────────────────────────────
    def load(self, game_state, exchange_queue=None):
        """Démarre la phase d'échange"""
        self._game_state = game_state

        if exchange_queue is not None:
            self._exchange_queue = list(exchange_queue)
        else:
            self._exchange_queue = []
            # Construire la file des échanges à faire
            for team_color in ["rouge", "bleu"]:
                team = game_state.get_team(team_color)
                if team.rouges > 0:
                    for _ in range(team.rouges):
                        self._exchange_queue.append(team_color)

        if not self._exchange_queue:
            # Rien à échanger
            QTimer.singleShot(500, self.exchanges_done)
            return

        self._process_next_exchange()

    def _process_next_exchange(self):
        """Traite le prochain échange de la file"""
        if not self._exchange_queue:
            # Tous les échanges terminés
            QTimer.singleShot(600, self.exchanges_done)
            return

        self._pending_team = self._exchange_queue.pop(0)
        self._exchanges_left = 1
        self._phase_take = True
        self._selected_take = []
        self._selected_give = []

        penalized = self._game_state.get_team(self._pending_team)
        adversary_color = "bleu" if self._pending_team == "rouge" else "rouge"
        adversary = self._game_state.get_team(adversary_color)

        color_pen = COLOR_ROUGE if self._pending_team == "rouge" else COLOR_BLEU
        self.instruction_lbl.setText(
            f"⚠️  {penalized.name} a un carton rouge — "
            f"{adversary.name} choisit 1 joueur à prendre"
        )
        self.instruction_lbl.setStyleSheet(f"""
            background-color: rgba({'220,30,30' if self._pending_team == 'rouge' else '30,80,220'},0.2);
            color: white; font-size: 14px; font-weight: bold;
            border: 2px solid {color_pen}; border-radius: 12px;
        """)
        self.counter_lbl.setText("Sélectionnez 1 joueur à prendre (adversaire choisit)")

        # Afficher les équipes - adversaire peut sélectionner dans l'équipe pénalisée
        self._build_team_cards(
            penalized=penalized,
            adversary=adversary,
            selecting_from_penalized=True   # adversaire prend dans pénalisé
        )

    def _build_team_cards(self, penalized, adversary, selecting_from_penalized: bool):
        """Construit les grilles de cartes"""
        self._cards_take = []
        self._cards_give = []

        # Vider les grilles
        for lay in [self.left_grid_lay, self.right_grid_lay]:
            while lay.count():
                item = lay.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        penalized_is_rouge = (self._pending_team == "rouge")
        adv_color = "bleu" if penalized_is_rouge else "rouge"

        # Gauche = rouge, Droite = bleue
        rouge_team = penalized if penalized_is_rouge else adversary
        bleu_team  = adversary if penalized_is_rouge else penalized
        rouge_selectable = penalized_is_rouge and selecting_from_penalized
        bleu_selectable  = not penalized_is_rouge and selecting_from_penalized

        self.left_title.setText(f"🔴  {rouge_team.name}")
        self.right_title.setText(f"🔵  {bleu_team.name}")

        for i, player in enumerate(rouge_team.players):
            card = MiniPlayerCard(
                player, selectable=rouge_selectable,
                border_color=COLOR_ROUGE
            )
            if rouge_selectable:
                card.toggled_card.connect(self._on_card_toggled)
                self._cards_take.append(card)
            row, col = divmod(i, 2)
            self.left_grid_lay.addWidget(card, row, col)

        for i, player in enumerate(bleu_team.players):
            card = MiniPlayerCard(
                player, selectable=bleu_selectable,
                border_color=COLOR_BLEU
            )
            if bleu_selectable:
                card.toggled_card.connect(self._on_card_toggled)
                self._cards_take.append(card)
            row, col = divmod(i, 2)
            self.right_grid_lay.addWidget(card, row, col)

        self.confirm_btn.setEnabled(False)
        self._selected_take = []

    def _on_card_toggled(self, player, selected: bool):
        """Gère la sélection/déselection d'une carte"""
        need = self._exchanges_left

        if self._phase_take:
            # Phase "adversaire prend"
            if selected:
                if len(self._selected_take) >= need:
                    # Désélectionner le dernier
                    self._selected_take[-1].reset_selection()
                    self._selected_take[-1]._selected = False
                    old = self._selected_take.pop()
                self._selected_take.append(
                    next(c for c in self._cards_take if c.player is player)
                )
            else:
                self._selected_take = [
                    c for c in self._selected_take if c.player is not player
                ]
            count = len(self._selected_take)
            self.counter_lbl.setText(
                f"Sélectionné : {count} / {need} joueur(s)"
            )
            self.confirm_btn.setEnabled(count == need)
        else:
            # Phase "pénalisé donne en retour"
            if selected:
                if len(self._selected_give) >= need:
                    self._selected_give[-1].reset_selection()
                    self._selected_give[-1]._selected = False
                    self._selected_give.pop()
                self._selected_give.append(
                    next(c for c in self._cards_give if c.player is player)
                )
            else:
                self._selected_give = [
                    c for c in self._selected_give if c.player is not player
                ]
            count = len(self._selected_give)
            self.counter_lbl.setText(
                f"Sélectionné : {count} / {need} joueur(s)"
            )
            self.confirm_btn.setEnabled(count == need)

    def _on_confirm(self):
        """Confirme la sélection courante"""
        if self._phase_take:
            # Étape 1 : adversaire a choisi quels joueurs prendre
            players_to_take = [c.player for c in self._selected_take]

            # Maintenant l'équipe pénalisée doit donner en retour
            self._phase_take = False
            penalized = self._game_state.get_team(self._pending_team)
            adversary_color = "bleu" if self._pending_team == "rouge" else "rouge"
            adversary = self._game_state.get_team(adversary_color)

            self.instruction_lbl.setText(
                f"🔄  {adversary.name} choisit {len(players_to_take)} joueur(s) à donner en échange"
            )
            self.counter_lbl.setText(
                f"Sélectionnez {len(players_to_take)} joueur(s) à donner en échange"
            )
            self.confirm_btn.setEnabled(False)
            self._selected_give = []

            # Reconstruire : adversaire sélectionne dans sa propre équipe
            self._build_team_cards_give(
                penalized=penalized,
                adversary=adversary,
                players_taken=players_to_take,
                n_to_give=len(players_to_take)
            )
        else:
            # Étape 2 : effectuer l'échange réel
            self._do_exchange()

    def _build_team_cards_give(self, penalized, adversary, players_taken, n_to_give):
        """Phase 2 : l'adversaire sélectionne ses propres joueurs à donner en échange"""
        self._cards_give = []
        penalized_is_rouge = (self._pending_team == "rouge")
        adv_color = "bleu" if penalized_is_rouge else "rouge"

        # Vider les grilles
        for lay in [self.left_grid_lay, self.right_grid_lay]:
            while lay.count():
                item = lay.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # Équipe adverse : sélectionnable (donne ses joueurs en échange)
        # Équipe pénalisée : affiche ses joueurs restants
        rouge_team = penalized if penalized_is_rouge else adversary
        bleu_team  = adversary if penalized_is_rouge else penalized

        self.left_title.setText(f"🔴  {rouge_team.name}")
        self.right_title.setText(f"🔵  {bleu_team.name}")

        for i, player in enumerate(rouge_team.players):
            is_adv = not penalized_is_rouge
            card = MiniPlayerCard(
                player, selectable=is_adv,
                border_color=COLOR_ROUGE
            )
            if is_adv:
                card.toggled_card.connect(self._on_card_toggled)
                self._cards_give.append(card)
            row, col = divmod(i, 2)
            self.left_grid_lay.addWidget(card, row, col)

        for i, player in enumerate(bleu_team.players):
            is_adv = penalized_is_rouge
            card = MiniPlayerCard(
                player, selectable=is_adv,
                border_color=COLOR_BLEU
            )
            if is_adv:
                card.toggled_card.connect(self._on_card_toggled)
                self._cards_give.append(card)
            row, col = divmod(i, 2)
            self.right_grid_lay.addWidget(card, row, col)

        self._players_taken = players_taken
        self._n_to_give = n_to_give

    def _do_exchange(self):
        """Effectue l'échange réel dans le GameState"""
        players_taken = self._players_taken
        players_given = [c.player for c in self._selected_give]

        penalized     = self._game_state.get_team(self._pending_team)
        adv_color     = "bleu" if self._pending_team == "rouge" else "rouge"
        adversary     = self._game_state.get_team(adv_color)

        # Retirer joueurs pris de l'équipe pénalisée → adversaire
        for p in players_taken:
            if p in penalized.players:
                penalized.players.remove(p)
                adversary.players.append(p)

        # Retirer joueurs donnés de l'adversaire → pénalisé
        for p in players_given:
            if p in adversary.players:
                adversary.players.remove(p)
                penalized.players.append(p)

        print(f"[Exchange] {penalized.name} ↔ {adversary.name} : échange effectué")

        QTimer.singleShot(800, self._process_next_exchange)
