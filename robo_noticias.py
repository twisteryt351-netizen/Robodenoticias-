import os
import random
import time
import feedparser
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURAÇÕES (variáveis de ambiente) ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BLOGGER_ID = os.environ.get("BLOGGER_ID")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

for nome, valor in [
    ("GROQ_API_KEY", GROQ_API_KEY),
    ("BLOGGER_ID", BLOGGER_ID),
    ("BLOGGER_CLIENT_ID", CLIENT_ID),
    ("BLOGGER_CLIENT_SECRET", CLIENT_SECRET),
    ("BLOGGER_REFRESH_TOKEN", REFRESH_TOKEN),
]:
    if not valor:
        raise ValueError(f"Faltou configurar a variável/segredo: {nome}")

groq_client = Groq(api_key=GROQ_API_KEY)

# --- FONTES RSS ---
FONTES = {
    "G1": "https://g1.globo.com/rss/g1/",
    "G1 Tecnologia": "https://g1.globo.com/rss/g1/tecnologia/",
    "UOL Notícias": "https://rss.uol.com.br/feed/noticias.xml",
    "Terra Notícias": "https://terra.com.br/rss/noticias/",
    "R7 Notícias": "https://noticias.r7.com/feed/",
    "Band Notícias": "https://band.com.br/rss/noticias/",
    "BBC Brasil": "https://www.bbc.com/portuguese/index.xml",
    "Folha de S.Paulo": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
    "O Globo": "https://oglobo.globo.com/rss/",
    "Veja": "https://veja.abril.com.br/feed/",
    "Globo Esporte": "https://ge.globo.com/rss/",
    "Omelete": "https://www.omelete.com.br/sitemap-news.xml",
    "TecMundo": "https://tecmundo.com.br/feed/",
    "Canaltech": "https://canaltech.com.br/feed/",
    "Quem Acontece": "https://quem.globo.com/rss/",
    "BBC News (Mundo)": "http://feeds.bbci.co.uk/news/world/rss.xml",
}

ARQUIVO_HISTORICO = "historico_postados.txt"

def ja_foi_postada(link):
    if not os.path.exists(ARQUIVO_HISTORICO):
        return False
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        return link in f.read()

def marcar_como_postada(link):
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def pegar_noticia_multiplas_fontes():
    fontes_lista = list(FONTES.items())
    random.shuffle(fontes_lista)
    tentativas = 0
    max_tentativas = 50

    for nome_fonte, url_rss in fontes_lista:
        try:
            feed = feedparser.parse(url_rss, agent="Mozilla/5.0")
        except Exception as e:
            continue

        for entrada in feed.entries[:5]:
            tentativas += 1
            if tentativas > max_tentativas:
                return None, None, None, None

            link = entrada.get("link")
            titulo = entrada.get("title")
            resumo = entrada.get("summary") or entrada.get("description") or ""

            if not link or not titulo:
                continue

            if not ja_foi_postada(link):
                print(f"✅ Notícia inédita encontrada em {nome_fonte}: {titulo[:60]}...")
                return titulo, resumo, link, nome_fonte

    return None, None, None, None

def gerar_imagem_gratis():
    # Gerador Picsum com seed aleatório (100% funcional)
    seed = random.randint(1, 1000)
    return f"https://picsum.photos/seed/{seed}/800/400"

def pedir_ia_groq(prompt):
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    prompt_texto = f"""
    Você é um jornalista de um portal popular no Brasil. 
    Escreva um artigo de notícia completo e descontraído em Português do Brasil com base no tema abaixo.

    REGRAS DE FORMATO E CONTEÚDO OBRIGATÓRIAS:
    1. Responda APENAS em HTML puro (use tags <p>, <h2>, <strong>, <ul>, <li>, <a>). NÃO USE MARKDOWN (nunca use **, #, ou lista de links no final).
    2. Escreva um texto longo, bem explicado e fluido (mínimo 800 palavras).
    3. Espalhe naturalmente DENTRO dos parágrafos do texto (sem criar uma lista no final) os seguintes links usando a tag HTML <a href="..." target="_blank">:
       - Para ofertas variadas: <a href="http://s.shopee.com.br/5VQHqQtgyf" target="_blank">confira esta seleção especial</a>
       - Para novidades do blog: <a href="http://cabinepopnews.blogspot.com" target="_blank">acesse mais notícias exclusivas</a>
       - Para dicas e loja: <a href="http://solucaodigitalshop.blogspot.com" target="_blank">veja as novidades aqui</a>
       - Para produtos em destaque: <a href="http://s.shopee.com.br/2qTBX58t8P" target="_blank">garanta descontos agora</a>
    4. Inclua 3 subtítulos <h2> ao longo do artigo.
    5. Insira 3 notas bem-humoradas do autor destacadas com <p><em>(Nota do autor: ...)</em></p>.

    Notícia Original ({nome_fonte}):
    Título: {titulo}
    Resumo: {resumo}
    """

    conteudo_reescrito = pedir_ia_groq(prompt_texto)

    prompt_titulo = (
        f"Crie um título inédito, sem aspas, chamativo e em português para esta notícia: '{titulo}'. "
        f"Responda APENAS com o título em texto puro, sem tags."
    )
    novo_titulo = pedir_ia_groq(prompt_titulo).replace('"', '').replace('\n', ' ').strip()

    img_url = gerar_imagem_gratis()

    html_final = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{img_url}" alt="{novo_titulo}" style="max-width:100%; height:auto; border-radius:8px;"/>
    </div>
    {conteudo_reescrito}
    <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
    <p style="font-size: 12px; color: gray; font-style: italic;">
        Fonte original: <a href="{link_fonte}" target="_blank" rel="noopener">{nome_fonte}</a>.
    </p>
    """

    return novo_titulo, html_final

def obter_credenciais():
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return creds

def publicar_no_blogger(titulo, conteudo):
    creds = obter_credenciais()
    blogger = build('blogger', 'v3', credentials=creds)

    corpo_postagem = {
        'kind': 'blogger#post',
        'title': titulo,
        'content': conteudo
    }

    resultado = blogger.posts().insert(blogId=BLOGGER_ID, body=corpo_postagem).execute()
    print(f"🔥 Sucesso! Post criado: '{titulo}' -> {resultado.get('url')}")

if __name__ == "__main__":
    print("🚀 Iniciando busca por notícia inédita...")
    titulo, resumo, link, fonte = pegar_noticia_multiplas_fontes()

    if titulo:
        print(f"📰 Notícia original: {titulo[:100]}...")
        try:
            novo_titulo, html_postagem = reescrever_com_ia_anti_plagio(titulo, resumo, link, fonte)
            print("✍️ Conteúdo gerado com sucesso via Groq. Publicando...")
            publicar_no_blogger(novo_titulo, html_postagem)
            marcar_como_postada(link)
            print("✅ Processo concluído.")
        except Exception as e:
            print(f"❌ Erro durante a geração ou publicação: {e}")
    else:
        print("❌ Nenhuma notícia nova disponível no momento.")
