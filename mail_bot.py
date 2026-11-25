import os
import base64
import json
import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration
load_dotenv('API.env')
API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

# ⚠️ ATTENTION : On passe en mode 'modify' pour pouvoir agir sur les emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def extraire_corps(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            data = extraire_corps(part)
            if data:
                return data
    elif payload.get('body', {}).get('data'):
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data).decode('utf-8')
    return ""

def creer_label_si_absent(service, nom_label):
    """Crée une étiquette (label) dans Gmail si elle n'existe pas."""
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'].lower() == nom_label.lower():
            return label['id']
    
    # Si le label n'existe pas, on le crée
    label_body = {
        'name': nom_label,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    new_label = service.users().labels().create(userId='me', body=label_body).execute()
    return new_label['id']

def analyser_email_ia(sujet, expediteur, corps):
    print(f"🧠 Analyse IA de : {sujet[:40]}...")
    
    prompt = f"""Tu es un assistant de gestion d'emails.
Analyse cet email :
Expéditeur : {expediteur}
Sujet : {sujet}
Corps : {corps[:1000]}

Réponds STRICTEMENT en JSON avec les clés :
- 'categorie' : 'Urgent', 'Client', 'Facture', 'Newsletter', ou 'Spam'.
- 'resume' : une phrase résumant l'email.
- 'action_suggeree' : ce que je devrais faire (ex: 'Répondre', 'Archiver', 'Ignorer').
"""
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        contenu = response.json()['choices'][0]['message']['content'].replace("```json", "").replace("```", "").strip()
        return json.loads(contenu)
    except Exception as e:
        print(f"  ❌ Erreur API DeepSeek : {e}")
        return None

def main():
    print("🚀 Connexion à Gmail...")
    service = get_gmail_service()
    
    # Récupérer les 3 derniers emails non lus
    results = service.users().messages().list(userId='me', q='is:unread', maxResults=3).execute()
    messages = results.get('messages', [])

    if not messages:
        print("📭 Aucun email non lu.")
        return

    print(f"📧 {len(messages)} emails non lus trouvés. Traitement en cours...\n")

    # On crée les labels nécessaires à l'avance
    print("🏷️ Vérification des étiquettes...")
    label_newsletter = creer_label_si_absent(service, "IA-Newsletter")
    label_urgent = creer_label_si_absent(service, "IA-Urgent")
    label_client = creer_label_si_absent(service, "IA-Client")

    for msg in messages:
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = txt['payload']
        headers = payload['headers']

        sujet = next((h['value'] for h in headers if h['name'] == 'Subject'), "Sans sujet")
        expediteur = next((h['value'] for h in headers if h['name'] == 'From'), "Inconnu")
        corps = extraire_corps(payload)

        analyse = analyser_email_ia(sujet, expediteur, corps)
        
        if analyse:
            categorie = analyse.get('categorie')
            print("=" * 50)
            print(f"📧 Sujet : {sujet}")
            print(f"🏷️  Catégorie : {categorie}")
            
            # --- LOGIQUE D'ACTION ---
            if categorie == "Spam":
                print("🗑️ Action : Déplacement à la corbeille.")
                service.users().messages().trash(userId='me', id=msg['id']).execute()
                
            elif categorie == "Newsletter":
                print("🏷️ Action : Application de l'étiquette 'IA-Newsletter' et marquage comme lu.")
                service.users().messages().modify(
                    userId='me', 
                    id=msg['id'], 
                    body={'addLabelIds': [label_newsletter], 'removeLabelIds': ['UNREAD']}
                ).execute()

            elif categorie in ["Urgent", "Client", "Facture"]:
                print(f"⚠️ Action : Marquage avec l'étiquette 'IA-{categorie}'.")
                label_id = label_urgent if categorie == "Urgent" else (label_client if categorie == "Client" else label_urgent)
                service.users().messages().modify(
                    userId='me', 
                    id=msg['id'], 
                    body={'addLabelIds': [label_id], 'removeLabelIds': ['UNREAD']}
                ).execute()
            
            print("=" * 50 + "\n")

if __name__ == "__main__":
    main()