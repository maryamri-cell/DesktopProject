# ============================================================
# ui/formation_screen.py — Gestion tactique de l'équipe
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QFrame, QGridLayout)
from PyQt5.QtCore    import Qt, pyqtSignal
from PyQt5.QtGui     import QFont, QColor, QPainter, QBrush, QPen
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config  import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU, COLOR_GRAY, COLOR_WHITE

class PlayerSlot(QFrame):
    """Bouton/Slot représentant un joueur sur le terrain"""
    clicked = pyqtSignal(str) # position name

    def __init__(self, pos_name: str, label: str, parent=None):
        super().__init__(parent)
        self.pos_name = pos_name
        self.label_text = label
        self.player = None
        self.setFixedSize(110, 80)
        self._setup_ui()

    def _setup_ui(self):
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(4, 4, 4, 4)
        self.lay.setSpacing(2)

        self.name_lbl = QLabel(self.label_text)
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.lay.addWidget(self.name_lbl)

        self.player_lbl = QLabel("Vide")
        self.player_lbl.setAlignment(Qt.AlignCenter)
        self.player_lbl.setStyleSheet("color: white; font-size: 11px; font-weight: 500;")
        self.player_lbl.setWordWrap(True)
        self.lay.addWidget(self.player_lbl)

        self.setStyleSheet("""
            PlayerSlot {
                background-color: rgba(0,0,0,0.5);
                border: 1px dashed #444;
                border-radius: 8px;
            }
            PlayerSlot:hover {
                background-color: rgba(255,255,255,0.1);
                border-color: white;
            }
        """)

    def set_player(self, player):
        self.player = player
        if player:
            self.player_lbl.setText(player.name)
            self.name_lbl.setStyleSheet("color: #00e676; font-size: 10px; font-weight: bold;")
            self.setStyleSheet("""
                PlayerSlot {
                    background-color: rgba(0,230,118,0.1);
                    border: 2px solid #00e676;
                    border-radius: 8px;
                }
            """)
        else:
            self.player_lbl.setText("Vide")
            self.name_lbl.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
            self.setStyleSheet("PlayerSlot { background-color: rgba(0,0,0,0.5); border: 1px dashed #444; border-radius: 8px; }")

    def mousePressEvent(self, event):
        self.clicked.emit(self.pos_name)

class FormationScreen(QWidget):
    """Écran de formation interactif"""
    done_clicked = pyqtSignal()
    move_requested = pyqtSignal(object, str) # Player, target_pos

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_player = None
        self._setup_ui()

    def _setup_ui(self):
        self.main_lay = QVBoxLayout(self)
        
        # Titre
        self.title_lbl = QLabel("GESTION TACTIQUE")
        self.title_lbl.setStyleSheet("color: white; font-size: 24px; font-weight: 900; letter-spacing: 2px;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.main_lay.addWidget(self.title_lbl)

        # Terrain
        self.pitch = QFrame()
        self.pitch.setObjectName("Pitch")
        self.pitch.setStyleSheet("""
            #Pitch {
                background-color: #1a3c1a;
                border: 3px solid #2e5a2e;
                border-radius: 20px;
                background-image: radial-gradient(circle, #2e5a2e 1px, transparent 1px);
                background-size: 40px 40px;
            }
        """)
        self.pitch_lay = QGridLayout(self.pitch)
        self.main_lay.addWidget(self.pitch, 4)

        # Créer les slots sur le terrain (Formation 5-2-3 ou similaire)
        self.slots = {}
        positions = [
            ("GK", "Gardien", 6, 2),
            ("DEF1", "Déf Gauche", 4, 0), ("DEF2", "Déf Central", 4, 1), ("DEF3", "Libéro", 4, 2), ("DEF4", "Déf Central", 4, 3), ("DEF5", "Déf Droit", 4, 4),
            ("MID1", "Milieu G", 2, 1), ("MID2", "Milieu D", 2, 3),
            ("ATT1", "Att Gauche", 0, 0), ("ATT2", "Buteur", 0, 2), ("ATT3", "Att Droit", 0, 4)
        ]

        for pos_id, label, r, c in positions:
            slot = PlayerSlot(pos_id, label)
            slot.clicked.connect(self._on_slot_clicked)
            self.pitch_lay.addWidget(slot, r, c, Qt.AlignCenter)
            self.slots[pos_id] = slot

        # Zone Remplaçants
        self.bench_frame = QFrame()
        self.bench_frame.setFixedHeight(120)
        self.bench_frame.setStyleSheet("background: #111; border-top: 2px solid #333;")
        self.bench_lay = QHBoxLayout(self.bench_frame)
        self.bench_lay.addWidget(QLabel("REMPLAÇANTS : "))
        self.bench_container = QHBoxLayout()
        self.bench_lay.addLayout(self.bench_container)
        self.main_lay.addWidget(self.bench_frame)

        # Bouton Continuer
        self.btn_done = QPushButton("VALIDER LA TACTIQUE")
        self.btn_done.setFixedHeight(50)
        self.btn_done.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_GREEN};
                color: black;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: #00c853; }}
        """)
        self.btn_done.clicked.connect(self.done_clicked)
        self.main_lay.addWidget(self.btn_done)

    def load_team(self, team_state):
        """Remplit le terrain avec les joueurs actuels"""
        # Nettoyer
        for slot in self.slots.values():
            slot.set_player(None)
        
        # Placer titulaires
        for pos_id, player in team_state.formation.items():
            if pos_id in self.slots:
                self.slots[pos_id].set_player(player)

        # Placer remplaçants
        # (Nettoyage de la zone remplaçants non illustré ici par soucis de simplicité, 
        # mais on viderait le layout bench_container)
        
    def _on_slot_clicked(self, pos_id):
        print(f"Slot cliqué : {pos_id}")
        # Logique de swap ou sélection ici
