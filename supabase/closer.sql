-- Closer : base de données Supabase (projet « Closer », séparé de Lift).
-- À exécuter une fois dans Supabase › SQL Editor › New query › Run.

-- 1. Les éléments de chaque utilisateur (tâches, devoirs, habitudes, objectifs, notes, réglages).
--    Une ligne par élément ; une suppression est gardée (deleted = true) pour se propager aux autres appareils.
create table if not exists public.closer_items (
  user_id uuid not null references auth.users(id) on delete cascade,
  id text not null,
  data jsonb,
  deleted boolean not null default false,
  updated_at bigint not null default 0,          -- heure du serveur, en millisecondes
  primary key (user_id, id)
);
create index if not exists closer_items_sync on public.closer_items (user_id, updated_at);

-- L'heure de modification est posée par le serveur (et non par le téléphone),
-- pour que la synchronisation ne dépende pas de l'heure des appareils.
create or replace function public.closer_touch() returns trigger language plpgsql set search_path = '' as $$
begin
  new.updated_at := (extract(epoch from clock_timestamp()) * 1000)::bigint;
  return new;
end $$;
drop trigger if exists closer_items_touch on public.closer_items;
create trigger closer_items_touch before insert or update on public.closer_items
  for each row execute function public.closer_touch();

-- Chacun ne voit et ne modifie que ses propres éléments.
alter table public.closer_items enable row level security;
drop policy if exists "closer lire" on public.closer_items;
drop policy if exists "closer creer" on public.closer_items;
drop policy if exists "closer modifier" on public.closer_items;
drop policy if exists "closer supprimer" on public.closer_items;
create policy "closer lire" on public.closer_items for select using ((select auth.uid()) = user_id);
create policy "closer creer" on public.closer_items for insert with check ((select auth.uid()) = user_id);
create policy "closer modifier" on public.closer_items for update using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "closer supprimer" on public.closer_items for delete using ((select auth.uid()) = user_id);

-- 2. Bouton « Supprimer mon compte » (efface le compte et toutes ses lignes).
create or replace function public.delete_my_account()
returns void language sql security definer set search_path = '' as $$
  delete from auth.users where id = auth.uid();
$$;
revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;

-- 3. Statistiques anonymes (aucun contenu, aucun lien avec les comptes).
--    open = ouverture (1 fois par jour et par appareil), first_item = premier élément créé,
--    active = jour où au moins une tâche est cochée, signup = compte créé.
create table if not exists public.closer_events (
  id bigint generated always as identity primary key,
  aid uuid not null,
  ev text not null check (ev in ('open','first_item','active','signup')),
  d date not null,
  v text,
  created_at timestamptz not null default now()
);
alter table public.closer_events enable row level security;
drop policy if exists "ajout anonyme" on public.closer_events;
create policy "ajout anonyme" on public.closer_events for insert to anon, authenticated with check (true);
grant insert on public.closer_events to anon, authenticated;

-- ===== Indicateurs (à lancer quand tu veux les voir) =====
-- Entonnoir : visiteurs -> premier élément -> compte
-- select count(distinct aid) filter (where ev='open') as visiteurs,
--        count(distinct aid) filter (where ev='first_item') as premier_element,
--        count(distinct aid) filter (where ev='signup') as comptes
-- from public.closer_events;

-- Utilisateurs actifs par semaine (au moins une tâche cochée)
-- select date_trunc('week', d)::date as semaine, count(distinct aid) as actifs
-- from public.closer_events where ev='active' group by 1 order by 1 desc;
