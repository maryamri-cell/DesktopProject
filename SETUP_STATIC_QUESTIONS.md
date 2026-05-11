# ✅ INSTRUCTIONS - Questions Statiques (API Limite Atteinte)

## 📋 Étape 1: Exécuter le SQL dans Supabase

Ouvre: https://supabase.com → Ton projet → SQL Editor

**Copie-colle ce SQL complet:**

```sql
-- ============================================================
-- Table de questions statiques (limite API atteinte)
-- ============================================================

create table if not exists public.static_questions (
    id uuid primary key default gen_random_uuid(),
    question_number integer not null unique,
    question text not null,
    options text[] not null,
    correct_answer text not null,
    difficulty text not null check (difficulty in ('easy', 'medium', 'hard')),
    created_at timestamptz not null default now()
);

alter table public.static_questions enable row level security;

drop policy if exists "static_questions_select" on public.static_questions;
create policy "static_questions_select"
on public.static_questions
for select
using (true);

insert into public.static_questions (question_number, question, options, correct_answer, difficulty) values
(1, 'Quel club a remporté le plus de Ligue des Champions?', ARRAY['Real Madrid', 'Bayern Munich', 'AC Milan', 'Liverpool'], 'Real Madrid', 'easy'),
(2, 'En quelle année Pelé a remporté son premier World Cup?', ARRAY['1954', '1958', '1962', '1970'], '1958', 'easy'),
(3, 'Quel joueur a remporté le Ballon d''Or le plus de fois?', ARRAY['Cristiano Ronaldo', 'Zinédine Zidane', 'Pelé', 'Diego Maradona'], 'Cristiano Ronaldo', 'medium'),
(4, 'Quel pays a remporté la Coupe du Monde 2018?', ARRAY['Belgique', 'France', 'Croatie', 'Allemagne'], 'France', 'easy'),
(5, 'Quel club de Manchester a le plus de Ligue des Champions?', ARRAY['Manchester United', 'Manchester City', 'Les deux en ont gagné 0', 'Manchester United en a 2'], 'Manchester United', 'medium'),
(6, 'Combien de Ballons d''Or a remporté Messi?', ARRAY['6', '7', '8', '5'], '8', 'medium'),
(7, 'Quel joueur a marqué le plus de buts en Ligue 1 français?', ARRAY['Thierry Henry', 'Kylian Mbappé', 'Edinson Cavani', 'Alexandre Lacazette'], 'Thierry Henry', 'medium'),
(8, 'En quelle année le FC Barcelone a remporté la Ligue des Champions?', ARRAY['2008, 2009, 2011, 2015', 'Toutes ces années', '2008 et 2009 seulement', 'Aucune de ces années'], 'Toutes ces années', 'hard'),
(9, 'Quel joueur a remporté la Coupe du Monde avec deux équipes différentes?', ARRAY['Gianfranco Zola', 'Maradona', 'Ronaldo Nazário', 'Aucun'], 'Ronaldo Nazário', 'hard'),
(10, 'Quel club a remporté le plus de titres de Premier League anglaise?', ARRAY['Manchester United', 'Liverpool', 'Arsenal', 'Chelsea'], 'Manchester United', 'easy'),
(11, 'Combien de fois la Nouvelle-Zélande a-t-elle remporté la Rugby World Cup?', ARRAY['0', '1', '2', '3'], '3', 'medium'),
(12, 'En quelle année Zinédine Zidane a-t-il retraité?', ARRAY['2004', '2005', '2006', '2007'], '2006', 'medium'),
(13, 'Quel joueur a marqué 5 buts dans un match de Ligue des Champions?', ARRAY['PSG vs Istanbul', 'Bayern vs Arsenal', 'PSG vs Istanbul Basaksehir', 'Juventus vs Lecce'], 'PSG vs Istanbul Basaksehir', 'hard'),
(14, 'Quel pays a organisé la Coupe du Monde 2014?', ARRAY['Brésil', 'Afrique du Sud', 'Allemagne', 'France'], 'Brésil', 'easy'),
(15, 'Quel joueur a remporté le plus de Ligue des Champions individuellement?', ARRAY['Paco Gento', 'Cristiano Ronaldo', 'Messi', 'Zinédine Zidane'], 'Cristiano Ronaldo', 'hard'),
(16, 'En quelle année le Bayern Munich a remporté 3 Ligue des Champions consécutives?', ARRAY['2019-2020-2021', '2020-2021-2022', '2021-2022-2023', 'Jamais'], '2019-2020-2021', 'hard'),
(17, 'Quel joueur français a marqué le plus de buts en International?', ARRAY['Thierry Henry', 'Kylian Mbappé', 'Olivier Giroud', 'Zinédine Zidane'], 'Olivier Giroud', 'medium'),
(18, 'Combien de fois l''Italie a remporté la Coupe du Monde?', ARRAY['2', '3', '4', '5'], '4', 'medium'),
(19, 'Quel joueur joue pour Manchester City depuis 2016?', ARRAY['Harry Styles', 'Raheem Sterling', 'David Silva', 'Sergio Agüero'], 'Raheem Sterling', 'easy'),
(20, 'En quelle année le Messi a rejonte Inter Miami?', ARRAY['2022', '2023', '2024', 'Il n''a pas rejoint'], '2023', 'easy'),
(21, 'Quel club a remporté la Ligue Europa 2022?', ARRAY['Francfort', 'Rangers', 'AS Rome', 'Séville'], 'Francfort', 'medium'),
(22, 'Combien de Coupes d''Afrique a remportées l''Égypte?', ARRAY['5', '6', '7', '8'], '7', 'medium'),
(23, 'Quel joueur a marqué dans 8 finales de Ligue des Champions?', ARRAY['Messi', 'Cristiano Ronaldo', 'Zinédine Zidane', 'Pelé'], 'Cristiano Ronaldo', 'hard'),
(24, 'En quelle année Cristiano Ronaldo a rejoint Juventus?', ARRAY['2017', '2018', '2019', '2020'], '2018', 'easy'),
(25, 'Quel club a remporté la Super Coupe d''Europe 2022?', ARRAY['Real Madrid', 'Manchester City', 'AS Rome', 'Liverpool'], 'Real Madrid', 'medium'),
(26, 'Nombre total de Coupes du Monde gagnée par la France?', ARRAY['1', '2', '3', '4'], '2', 'easy'),
(27, 'Quel joueur a marqué le plus de buts pour le Brésil?', ARRAY['Ronaldo', 'Ronaldinho', 'Pelé', 'Neymar'], 'Pelé', 'medium'),
(28, 'En quelle année l''Italie a remporté la Coupe d''Europe 2020?', ARRAY['2020', '2021', '2022', 'Jamais'], '2021', 'medium'),
(29, 'Quel joueur a joué le plus de matchs pour Barcelone?', ARRAY['Messi', 'Ronaldinho', 'Xavi', 'Iniesta'], 'Xavi', 'medium'),
(30, 'Combien de buts Messi a-t-il marqué pour Barcelone?', ARRAY['500+', '600+', '650+', '700+'], '650+', 'hard'),
(31, 'Quel club a remporté la Premier League 2022-2023?', ARRAY['Liverpool', 'Arsenal', 'Manchester City', 'Tottenham'], 'Manchester City', 'easy'),
(32, 'En quelle année Kylian Mbappé a-t-il rejoint le PSG?', ARRAY['2015', '2016', '2017', '2018'], '2017', 'easy'),
(33, 'Quel joueur a marqué le plus rapide but en Coupe du Monde?', ARRAY['Gerd Müller', 'Pelé', 'Cristiano Ronaldo', 'Diego Maradona'], 'Gerd Müller', 'hard'),
(34, 'Nombre de fois l''Allemagne a remporté la Coupe du Monde?', ARRAY['3', '4', '5', '6'], '4', 'medium'),
(35, 'Quel joueur a remporté le Ballon d''Or avec 3 clubs différents?', ARRAY['Ronaldo', 'Ronaldinho', 'Aucun', 'Zinédine Zidane'], 'Aucun', 'hard'),
(36, 'En quelle année Neymar a-t-il rejoint le PSG?', ARRAY['2016', '2017', '2018', '2019'], '2017', 'easy'),
(37, 'Quel club a remporté le plus de Coupe du Roi espagnole?', ARRAY['Real Madrid', 'FC Barcelone', 'Athletic Bilbao', 'Valencia'], 'FC Barcelone', 'medium'),
(38, 'Combien de Ballon d''Or a gagné Zinédine Zidane?', ARRAY['1', '2', '3', '4'], '1', 'easy'),
(39, 'Quel joueur a joué le plus de matchs internationaux?', ARRAY['Cristiano Ronaldo', 'Messi', 'Lothar Matthäus', 'Rafa Márquez'], 'Cristiano Ronaldo', 'medium'),
(40, 'En quelle année le PSG a remporté la Ligue 1 pour la première fois?', ARRAY['2012', '2013', '2014', '2015'], '2013', 'easy');
```

## 📝 Étape 2: Code Python mis à jour

### matchmaking_service.py
- ✅ Nouvelle méthode `get_static_questions()` pour charger les 40 questions
- ✅ `generate_and_save_match_questions()` maintenant charge les questions statiques (pas génération)

### main.py
- ✅ `_on_match_found()` appelle la nouvelle méthode
- ✅ `_build_questions()` simple récupération des 30 premières

### config.py
- ✅ `TOTAL_MANCHES = 30` (était 11)

---

## 🎮 Résultats attendus

**Flux du jeu:**
1. Joueur 1 accepte joueur 2 → **Match accepté**
2. Joueur 1 détecte acceptance → **Charge les 30 questions statiques** (pas API)
3. Sauvegarde dans `match_questions` table
4. Joueur 1 démarre le jeu → Récupère les 30 questions
5. Joueur 2 aussi détecte acceptance → Essaie charger, trouve déjà 30 en BD
6. Joueur 2 démarre le jeu → **Récupère les MÊMES 30 questions**

**Synchronisation du jeu:**
- ✅ **Même question** affichée sur les 2 écrans
- ✅ Un buzz → l'autre **attend** (pas peut buzzer)
- ✅ Mauvaise réponse → **2ème joueur a 2ème chance**
- ✅ Mauvaise aussi → Question **annulée** → prochaine question
- ✅ Bonne réponse → **Choix du joueur**

---

## ⚠️ Avantages

✅ **Pas de limite API** (jusqu'à 40 questions statiques)
✅ **Synchronisation garantie** (même BD pour les 2 joueurs)
✅ **Questions prévisibles** (test/debug facile)
✅ **0.5s latence réseau** (Supabase fiable)

---

## 🧪 Test maintenant

1. Exécute le SQL dans Console Supabase
2. Redémarre les 2 apps
3. Joueur 1 invite Joueur 2
4. Joueur 2 accepte
5. **Vérify:** Les deux voient "Manche 1/30" avec même question ✅

Teste maintenant! 🚀
