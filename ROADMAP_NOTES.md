# Roadmap Mithrid

Notes de roadmap conservees pour reference future.

## 1. Le Bloc "Inputs" (Ingestion)

C'est quoi ? Vos connecteurs n8n, vos scripts, vos APIs, vos fichiers bruts.

Le piege : Vouloir nettoyer la donnee des cette etape.

La regle : N'essayez pas de reflechir a Neo4j ici. Ce bloc doit uniquement recuperer la donnee brute et la passer proprement au bloc suivant.

## 2. Le Bloc "Organisation" (Le pont vers Neo4j)

C'est la boite noire qui vous inquiete, mais son fonctionnement est en realite tres mathematique. Neo4j ne comprend pas un texte brut ; il comprend uniquement des Noeuds (des entites) et des Relations (les liens entre elles).

Comment ca fonctionne ? On utilise ce qu'on appelle un Mappeur. C'est un script (souvent aide par une IA ou des regles n8n) qui prend votre input et le traduit en langage Cypher.

Exemple concret : Votre input dit : "Jean a achete l'action Apple le 30 juin". Le bloc d'organisation va extraire :

- Noeud 1 : `(p:Personne {nom: "Jean"})`
- Noeud 2 : `(a:Action {nom: "Apple"})`
- La Relation : `[:A_ACHETE {date: "2026-06-30"}]`

C'est ce bloc qui pousse ensuite ces elements dans Neo4j.

## 3. Le Bloc "IA / Interpretation" (Exploitation)

C'est quoi ? C'est un Agent IA (via Cursor ou des noeuds LLM avances dans n8n) a qui on donne un acces direct a Neo4j.

Son role : L'IA ne va pas simplement lire les lignes, elle va utiliser la puissance du graphe (les connexions indirectes) pour faire des deductions.

Exemple de correlation : L'IA remarque que chaque fois que le noeud Entreprise X subit une baisse, le noeud Entreprise Y (pourtant dans un autre secteur) baisse aussi 3 jours apres parce qu'elles partagent un meme fournisseur (Noeud Fournisseur Z).
