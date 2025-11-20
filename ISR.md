# ISR.md – isr-cli (Intentional Software Representation)

## Overview
Projet : CLI officiel pour la méthodologie ISR  
Objectif principal : transformer un document ISR passif en artefact actif qui orchestre le contexte et garde la cohérence sémantique entre intention et code.  
Le CLI ne modifie jamais le code lui-même. Il est un frontal strict et un vérificateur.

## Glossary
- ISR : Document Markdown source unique de vérité sémantique
- Frontal : outil qui injecte automatiquement l’ISR dans chaque appel LLM
- Check : vérification déterministe de cohérence code ↔ ISR
- Ask : commande qui ouvre une session LLM avec contexte complet

## Core Workflows
1. Developer asks → `isr ask "…"` → CLI charge ISR + code + diff → appelle LLM → retour réponse
2. Developer change code → `isr check` → CLI envoie (ISR + ancien code + nouveau code) à LLM → retourne dérives ou OK
3. New project → `isr new` → génère ISR.md pré-rempli via wizard
4. Legacy project → `isr bootstrap` → extrait intention du code existant

## Invariants (non négociables)
- Le CLI ne doit JAMAIS éditer de fichiers directement
- Le CLI ne doit JAMAIS appliquer de patchs sans validation humaine explicite
- Tout appel LLM doit contenir l’ISR intégral + le system prompt strict (fichier templates/system_prompt.txt)
- `isr check` doit échouer (exit code ≠ 0) s’il détecte une dérive d’intention
- Le CLI doit fonctionner sans aucune configuration (fallback sur Claude 3.5 Sonnet via ANTHROPIC_API_KEY ou OpenAI)

## Architectural Decisions
- Langage : Python ≥ 3.9 (distribution la plus simple)
- Dépendances minimales : click, rich, pydantic, httpx (≤ 5 deps)
- Pas de base de données, pas de serveur → tout en local
- Configuration via variables d’environnement uniquement
- Modèle par défaut configurable via --model (claude-3-5-sonnet-20241022 en priorité)

## Non-Goals (explicites)
- Devenir un agent autonome type Aider/Cursor → on laisse ça aux outils spécialisés
- Gérer l’édition de fichiers → on reste pur frontal/vérificateur
- Supporter 50 LLMs dès le jour 1 → on commence avec Claude + OpenAI + Grok + Ollama