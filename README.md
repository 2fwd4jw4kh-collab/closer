# Closer

Une application web personnelle pour organiser ses journées : agenda sur 7 jours, tâches, devoirs, habitudes et objectifs long terme, dans une seule page.

Elle fonctionne sans compte, sans serveur et sans abonnement. Les données restent dans le navigateur de l'appareil.

**Démo :** `https://VOTRE-PSEUDO.github.io/closer/`

## Pourquoi ce projet

Les applications existantes (to-do, agenda, suivi d'habitudes) séparaient ce que je voulais voir au même endroit : mes cours, mon job étudiant, mes habitudes et mes objectifs. J'ai donc défini mon propre outil, centré sur une question : que me reste-t-il à faire aujourd'hui ?

## Fonctionnalités

- **Jour** : le nombre de choses restantes aujourd'hui, une barre d'avancement et une bande des 7 prochains jours.
- **Devoirs** : par matière et par date de rendu, avec retards signalés.
- **Tâches** : catégories personnalisables, regroupement par date ou par catégorie, rangement manuel.
- **Habitudes** : quotidiennes (avec série de jours consécutifs) ou hebdomadaires (par exemple 3 séances par semaine).
- **Objectifs** : échéance, compte à rebours, étapes, et lien avec les tâches et habitudes qui les font avancer.
- **Brouillon** : pages de notes libres, enregistrées automatiquement.
- **Sauvegarde** : export et import des données dans un fichier.
- **Installable** : s'ajoute à l'écran d'accueil du téléphone et s'ouvre hors connexion.

## Choix techniques

- HTML, CSS et JavaScript, sans framework ni dépendance : un seul fichier `index.html`.
- Stockage local (`localStorage`), sans base de données ni compte utilisateur.
- Application web installable (manifeste et service worker).
- Interface pensée d'abord pour le téléphone, accessible au clavier et respectueuse du réglage « réduire les animations ».

## Démarche

J'ai conçu ce projet en dirigeant un assistant IA (Claude, d'Anthropic) : j'ai défini le besoin, les fonctionnalités et la direction visuelle, testé chaque version sur mon usage réel, puis fait corriger et évoluer l'application par itérations (critique d'ergonomie, refonte de la navigation, ajout de la sauvegarde). Le code a été généré par l'IA sous ma direction.

## Utilisation

Ouvrir la démo dans un navigateur. Sur téléphone, utiliser « Ajouter à l'écran d'accueil » pour l'installer comme une application.

Pour changer d'appareil : bouton **Sauvegarde**, exporter sur le premier appareil, importer sur le second.

## Limites connues

- Pas de synchronisation automatique entre appareils.
- Pas de notifications de rappel.
