import os

content = open('ui/matchmaking_screen.py', 'r', encoding='utf-8').read()

idx = content.find('    def _create_player_card')
end_marker = '    def _challenge_player'
end_idx = content.find(end_marker)

new_card = '''    def _create_player_card(self, player: dict) -> QFrame:
        card = QFrame()
        card.setFixedWidth(150)
        card.setFixedHeight(185)
        card.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            " stop:0 #1a2540, stop:1 #0d1525);"
            " border: 2px solid #00d4ff; border-radius: 14px; }"
            " QFrame:hover { border-color: #ffd700; }"
        )
        card.setCursor(Qt.PointingHandCursor)

        vlay = QVBoxLayout(card)
        vlay.setContentsMargins(10, 12, 10, 12)
        vlay.setSpacing(6)
        vlay.setAlignment(Qt.AlignHCenter)

        av = QLabel(player.get("avatar", "⚽"))
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet("font-size: 34px; background: transparent;")
        vlay.addWidget(av)

        nick = QLabel(player.get("nickname", "Joueur"))
        nick.setAlignment(Qt.AlignCenter)
        nick.setStyleSheet("color: white; font-weight: 900; font-size: 13px; background: transparent;")
        vlay.addWidget(nick)

        status = player.get("online_status", "offline")
        sc = "#00e676" if status == "online" else "#666"
        st = QLabel("ONLINE" if status == "online" else "OFFLINE")
        st.setAlignment(Qt.AlignCenter)
        st.setStyleSheet("color: {}; font-size: 10px; font-weight: 700; background: transparent;".format(sc))
        vlay.addWidget(st)

        vlay.addStretch()

        btn = QPushButton("DEFIER")
        btn.setFixedHeight(32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 #c5850a, stop:1 #8b5c1a); color: white;"
            " border: 2px solid #ffd700; border-radius: 8px;"
            " font-weight: 900; font-size: 12px; letter-spacing: 2px; }"
            " QPushButton:hover { background: #d4af37; }"
        )
        btn.clicked.connect(lambda: self._challenge_player(player))
        vlay.addWidget(btn)

        return card

'''

new_content = content[:idx] + new_card + content[end_idx:]
open('ui/matchmaking_screen.py', 'w', encoding='utf-8', newline='\n').write(new_content)
print("OK - player card updated, total chars:", len(new_content))
