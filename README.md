# Closer

Une application web personnelle pour organiser ses journées : agenda sur 7 jours, tâches, devoirs, habitudes et objectifs long terme, dans une seule page.

Elle fonctionne **sans compte** (données dans le navigateur de l'appareil) ou **avec un compte facultatif** pour retrouver ses éléments sur tous ses appareils.

**Application :** https://2fwd4jw4kh-collab.github.io/closer/

## Pourquoi ce projet

Les applications existantes (to-do, agenda, suivi d'habitudes) séparaient ce que je voulais voir au même endroit : mes cours, mon job étudiant, mes habitudes et mes objectifs. J'ai donc défini mon propre outil, centré sur une question : que me reste-t-il à faire aujourd'hui ?

## Fonctionnalités

- **Jour** : le nombre de choses restantes aujourd'hui, une barre d'avancement et une bande des 7 prochains jours.
- **Devoirs** : par matière et par date de rendu, avec retards signalés.
- **Tâches** : catégories personnalisables, regroupement par date ou par catégorie, rangement manuel.
- **Habitudes** : quotidiennes (avec série de jours consécutifs) ou hebdomadaires (par exemple 3 séances par semaine).
- **Objectifs** : échéance, compte à rebours, étapes, et lien avec les tâches et habitudes qui les font avancer.
- **Brouillon** : pages de notes libres, enregistrées automatiquement.
- **Compte facultatif** : connexion par e-mail et mot de passe, synchronisation automatique entre téléphone et ordinateur, suppression du compte en un geste.
- **Sauvegarde** : export et import des données dans un fichier.
- **Mises à jour** : un bandeau « Nouvelle version » apparaît dès qu'une version est mise en ligne.
- **Installable** : s'ajoute à l'écran d'accueil du téléphone et s'ouvre hors connexion.

## Choix techniques

| Sujet | Choix |
|---|---|
| Interface | HTML, CSS et JavaScript, sans framework : un seul fichier `index.html` |
| Stockage | `localStorage` sur l'appareil, toujours ; le compte s'y ajoute sans le remplacer |
| Comptes et synchro | Supabase (projet dédié à Closer) : authentification, base PostgreSQL, règles d'accès par utilisateur (RLS) |
| Synchronisation | Élément par élément : seuls les éléments modifiés sont envoyés ; les suppressions se propagent ; l'heure de modification est posée par le serveur pour ne pas dépendre de l'horloge des appareils |
| Hors ligne | Manifeste + service worker (réseau d'abord, cache en secours) |
| Qualité | Tests automatiques dans un vrai navigateur (Playwright) à chaque envoi sur GitHub |
| Accessibilité | Pensée d'abord pour le téléphone, utilisable au clavier, respecte « réduire les animations » |

## Structure

| Fichier | Rôle |
|---|---|
| `index.html` | Toute l'application, et son numéro de version (`APPV`) |
| `sw.js` | Mode hors ligne et mises à jour |
| `supabase/closer.sql` | Tables, règles d'accès, suppression de compte et statistiques (à exécuter une fois dans Supabase) |
| `tests/smoke.py` | Tests de fumée, avec un faux Supabase (aucun réseau nécessaire) |
| `.github/workflows/tests.yml` | Lance les tests à chaque envoi sur GitHub (onglet Actions) |

À chaque mise en ligne : changer `APPV` dans `index.html` et le nom du cache `CACHE` dans `sw.js`.

## Tests

```
python3 -m http.server 8766 &
python3 tests/smoke.py
```

Vérifie : fonctionnement sans compte, création de compte (mot de passe trop faible refusé), envoi des éléments locaux à la première connexion, récupération sur un second appareil, propagation d'un ajout et d'une suppression, déconnexion sans perte de données, statistiques désactivables, suppression du compte, bandeau de nouvelle version.

## Données et confidentialité

- **Sans compte**, rien ne quitte l'appareil.
- **Avec un compte**, l'adresse e-mail et les éléments sont stockés dans Supabase ; chaque compte ne peut lire que ses propres données.
- **Statistiques anonymes** : un identifiant tiré au hasard sur l'appareil, sans lien avec le compte ni le contenu, et seulement 4 événements (`open` une fois par jour, `first_item`, `active`, `signup`). Désactivables dans **Compte › À propos**.

## Démarche

J'ai conçu ce projet en dirigeant un assistant IA (Claude, d'Anthropic) : j'ai défini le besoin, les fonctionnalités et la direction visuelle, testé chaque version sur mon usage réel, puis fait corriger et évoluer l'application par itérations (critique d'ergonomie, refonte de la navigation, sauvegarde, comptes et synchronisation). Le code a été généré par l'IA sous ma direction.

## Limites connues

- Si un même élément est modifié sur deux appareils hors connexion, la version de l'appareil qui se synchronise en dernier est conservée.
- Pas de notifications de rappel.
