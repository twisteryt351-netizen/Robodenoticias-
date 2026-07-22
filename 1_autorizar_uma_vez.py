"""
RODAR ESTE ARQUIVO APENAS UMA VEZ, NO SEU COMPUTADOR.
Ele vai abrir o navegador para você fazer login no Google e permitir
que o robô publique no seu Blogger. Depois disso, você nunca mais
precisa rodar este arquivo de novo.

Antes de rodar, coloque o arquivo client_secrets.json (baixado do
Google Cloud Console) na mesma pasta deste script.
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/blogger']

flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
creds = flow.run_local_server(port=0)

dados = {
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "refresh_token": creds.refresh_token,
}

with open("credenciais_blogger.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, indent=2)

print("\n✅ Pronto! Foi criado o arquivo credenciais_blogger.json na sua pasta.")
print("Abra esse arquivo, você vai precisar copiar os 3 valores de dentro dele")
print("(client_id, client_secret, refresh_token) para colar no GitHub no próximo passo.\n")
