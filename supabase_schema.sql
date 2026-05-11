-- ============================================================
-- Supabase schema: profiles + score_history + matchmaking
-- ============================================================

create extension if not exists pgcrypto;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null unique,
    nickname text not null,
    avatar text not null default '⚽',
    online_status text not null default 'offline' check (online_status in ('online', 'offline')),
    last_seen timestamptz default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.match_invitations (
    id uuid primary key default gen_random_uuid(),
    from_user_id uuid not null references public.profiles(id) on delete cascade,
    to_user_id uuid not null references public.profiles(id) on delete cascade,
    status text not null default 'pending' check (status in ('pending', 'accepted', 'declined')),
    created_at timestamptz not null default now()
);

create table if not exists public.matches (
    id uuid primary key default gen_random_uuid(),
    player1_id uuid not null references public.profiles(id) on delete cascade,
    player2_id uuid not null references public.profiles(id) on delete cascade,
    player1_nickname text not null default 'Joueur 1',
    player2_nickname text not null default 'Joueur 2',
    status text not null default 'active' check (status in ('active', 'completed', 'cancelled')),
    questions_generated boolean not null default false,
    created_at timestamptz not null default now(),
    completed_at timestamptz
);

create table if not exists public.match_state (
    id uuid primary key default gen_random_uuid(),
    match_id uuid not null unique references public.matches(id) on delete cascade,
    round_number integer not null default 1,
    phase text not null default 'BUZZ' check (phase in ('BUZZ', 'ANSWER_A', 'SECOND_CHANCE_A', 'ANSWER_B', 'SECOND_CHANCE_B', 'PICK', 'REVEAL', 'END')),
    active_player_id uuid references public.profiles(id) on delete set null,
    last_answer_correct boolean,
    pick_index integer default null,
    updated_at timestamptz not null default now()
);

create table if not exists public.score_history (
    id bigint generated always as identity primary key,
    user_id uuid not null references public.profiles(id) on delete cascade,
    mode text not null,
    team_rouge_name text not null,
    team_bleu_name text not null,
    team_rouge_score integer not null,
    team_bleu_score integer not null,
    winner text not null check (winner in ('rouge', 'bleu', 'egalite')),
    created_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_profiles_updated_at on public.profiles;
create trigger trg_profiles_updated_at
before update on public.profiles
for each row
execute procedure public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.score_history enable row level security;

-- profiles: chaque utilisateur peut lire TOUS les profils (pour matchmaking)
-- mais peut modifier UNIQUEMENT son propre profil
drop policy if exists "profiles_select_all" on public.profiles;
create policy "profiles_select_all"
on public.profiles
for select
using (true);  -- Permettre de voir tous les profils

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own"
on public.profiles
for insert
with check (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
on public.profiles
for update
using (auth.uid() = id)
with check (auth.uid() = id);

-- history: chaque utilisateur lit/insere uniquement ses parties
drop policy if exists "history_select_own" on public.score_history;
create policy "history_select_own"
on public.score_history
for select
using (auth.uid() = user_id);

drop policy if exists "history_insert_own" on public.score_history;
create policy "history_insert_own"
on public.score_history
for insert
with check (auth.uid() = user_id);

-- ============================================================
-- match_invitations: utilisateurs peuvent envoyer/recevoir invitations
-- ============================================================
alter table public.match_invitations enable row level security;

drop policy if exists "invitations_select_own" on public.match_invitations;
create policy "invitations_select_own"
on public.match_invitations
for select
using (auth.uid() = from_user_id OR auth.uid() = to_user_id);

drop policy if exists "invitations_insert_own" on public.match_invitations;
create policy "invitations_insert_own"
on public.match_invitations
for insert
with check (auth.uid() = from_user_id);

drop policy if exists "invitations_update_own" on public.match_invitations;
create policy "invitations_update_own"
on public.match_invitations
for update
using (auth.uid() = to_user_id OR auth.uid() = from_user_id)
with check (auth.uid() = to_user_id OR auth.uid() = from_user_id);

-- ============================================================
-- matches: utilisateurs peuvent voir/modifier leurs matches
-- ============================================================
alter table public.matches enable row level security;

drop policy if exists "matches_select_own" on public.matches;
create policy "matches_select_own"
on public.matches
for select
using (auth.uid() = player1_id OR auth.uid() = player2_id);

drop policy if exists "matches_insert_own" on public.matches;
create policy "matches_insert_own"
on public.matches
for insert
with check (auth.uid() = player1_id OR auth.uid() = player2_id);

drop policy if exists "matches_update_own" on public.matches;
create policy "matches_update_own"
on public.matches
for update
using (auth.uid() = player1_id OR auth.uid() = player2_id)
with check (auth.uid() = player1_id OR auth.uid() = player2_id);

-- ============================================================
-- match_questions: Questions générées UNE FOIS par match
-- ============================================================
create table if not exists public.match_questions (
    id uuid primary key default gen_random_uuid(),
    match_id uuid not null references public.matches(id) on delete cascade,
    round_number integer not null,
    question text not null,
    options text[] not null,
    correct_answer text not null,
    difficulty text not null,
    created_at timestamptz not null default now(),
    unique(match_id, round_number)
);

alter table public.match_questions enable row level security;

drop policy if exists "match_questions_select" on public.match_questions;
create policy "match_questions_select"
on public.match_questions
for select
using (
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);

-- ============================================================
-- match_buzzes: Évènements de buzz en temps réel
-- ============================================================
create table if not exists public.match_buzzes (
    id uuid primary key default gen_random_uuid(),
    match_id uuid not null references public.matches(id) on delete cascade,
    round_number integer not null,
    player_id uuid not null references public.profiles(id) on delete cascade,
    timestamp timestamptz not null default now(),
    created_at timestamptz not null default now(),
    unique(match_id, round_number, player_id)
);

alter table public.match_buzzes enable row level security;

drop policy if exists "match_buzzes_select" on public.match_buzzes;
create policy "match_buzzes_select"
on public.match_buzzes
for select
using (
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);

drop policy if exists "match_buzzes_insert" on public.match_buzzes;
create policy "match_buzzes_insert"
on public.match_buzzes
for insert
with check (
    player_id = auth.uid() AND
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);

-- ============================================================
-- match_answers: Réponses des joueurs (synchronisation en temps réel)
-- ============================================================
create table if not exists public.match_answers (
    id uuid primary key default gen_random_uuid(),
    match_id uuid not null references public.matches(id) on delete cascade,
    round_number integer not null,
    player_id uuid not null references public.profiles(id) on delete cascade,
    chosen_answer text not null,
    is_correct boolean not null,
    score_gained integer not null default 0,
    timestamp timestamptz not null default now(),
    created_at timestamptz not null default now(),
    unique(match_id, round_number, player_id)  -- Un joueur ne peut répondre qu'une fois par round
);

alter table public.match_answers enable row level security;

drop policy if exists "match_answers_select" on public.match_answers;
create policy "match_answers_select"
on public.match_answers
for select
using (
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);

drop policy if exists "match_answers_insert" on public.match_answers;
create policy "match_answers_insert"
on public.match_answers
for insert
with check (
    player_id = auth.uid() AND
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);

-- ============================================================
-- match_state: État du jeu (phase, joueur actif, etc)
-- ============================================================
alter table public.match_state enable row level security;

drop policy if exists "match_state_select" on public.match_state;
create policy "match_state_select"
on public.match_state
for select
using (
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);

drop policy if exists "match_state_insert" on public.match_state;
create policy "match_state_insert"
on public.match_state
for insert
with check (
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);

drop policy if exists "match_state_update" on public.match_state;
create policy "match_state_update"
on public.match_state
for update
using (
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
)
with check (
    match_id IN (
        SELECT id FROM public.matches 
        WHERE player1_id = auth.uid() OR player2_id = auth.uid()
    )
);
