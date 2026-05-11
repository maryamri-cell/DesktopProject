-- Corrections pour la synchronisation du buzz
-- Problème: Les deux joueurs disent "L'AUTRE a buzzé EN PREMIER"
-- Solution: Ajouter une fonction pour déterminer le buzzer de manière DETERMINISTE

-- Ajouter une colonne pour stocker qui doit répondre
ALTER TABLE public.matches ADD COLUMN IF NOT EXISTS current_buzzer_id uuid REFERENCES public.profiles(id);

-- Fonction pour obtenir le VRAI premier buzz de manière deterministe
-- En cas d'égalité de timestamp, le plus petit ID gagne
CREATE OR REPLACE FUNCTION get_first_buzzer(p_match_id uuid, p_round integer)
RETURNS uuid AS $$
DECLARE
    buzzer_id uuid;
BEGIN
    SELECT player_id INTO buzzer_id
    FROM public.match_buzzes
    WHERE match_id = p_match_id AND round_number = p_round
    ORDER BY timestamp ASC, player_id ASC  -- timestamp, puis ID pour déterminisme
    LIMIT 1;
    
    RETURN buzzer_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- Créer un index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_match_buzzes_match_round 
ON public.match_buzzes(match_id, round_number, timestamp);

-- Vérifier: Afficher les buzzes du dernier match
-- SELECT player_id, timestamp FROM match_buzzes WHERE match_id = 'YOUR_MATCH_ID' ORDER BY timestamp;
