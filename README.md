\# Assistant Email IA (Gmail + DeepSeek) 📧🤖



Ce projet est un bot Python autonome qui se connecte à votre boîte Gmail, analyse les emails entrants via l'API DeepSeek, et agit automatiquement selon la catégorie détectée.



\## 🚀 Fonctionnalités

\- \*\*Connexion sécurisée\*\* : Utilisation d'OAuth 2.0 (Google API) sans stockage de mot de passe.

\- \*\*Classification IA\*\* : Détection des catégories (Spam, Urgent, Client, Newsletter, Facture).

\- \*\*Actions automatiques\*\* :

&#x20; - Spam → Déplacement à la corbeille.

&#x20; - Newsletter → Création et application d'une étiquette dédiée, marquage comme lu.

&#x20; - Client/Urgent → Marquage avec une étiquette prioritaire.



\## 🛠️ Prérequis

\- Python 3.9+

\- Un projet Google Cloud avec l'API Gmail activée et le scope `gmail.modify`.

\- Une clé API DeepSeek.



\## ⚙️ Installation

1\. Clonez le dépôt.

2\. Installez les dépendances : `pip install -r requirements.txt`

3\. Placez votre fichier `credentials.json` (Google) à la racine.

4\. Créez un fichier `API.env` avec : `DEEPSEEK\_API\_KEY=votre\_cle`

5\. Lancez : `python mail\_bot.py`



\## 💡 Cas d'usage

Idéal pour les professionnels submergés par les emails, les équipes support, ou pour intégrer une couche d'IA dans un CRM existant.

