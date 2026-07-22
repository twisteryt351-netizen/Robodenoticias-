import os
import random
import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURAÇÕES (tudo vem de variáveis de ambiente / GitHub Secrets) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOGGER_ID = os.environ.get("BLOGGER_ID")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

for nome, valor in [
    ("GEMINI_API_KEY", GEMINI_API_KEY),
    ("BLOGGER_ID", BLOGGER_ID),
    ("BLOGGER_CLIENT_ID", CLIENT_ID),
    ("BLOGGER_CLIENT_SECRET", CLIENT_SECRET),
    ("BLOGGER_REFRESH_TOKEN", REFRESH_TOKEN),
]:
    if not valor:
        raise ValueError(f"Faltou configurar a variável/segredo: {nome}")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- FONTES RSS: nacionais e internacionais ---
FONTES = {
    "G1": "https://g1.globo.com/rss/g1/",
    "G1 Tecnologia": "https://g1.globo.com/rss/g1/tecnologia/",
    "UOL Notícias": "https://rss.uol.com.br/feed/noticias.xml",
    "BBC News (Mundo)": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "CNN Internacional": "http://rss.cnn.com/rss/edition.rss",
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
    """Percorre as fontes em ordem aleatória e retorna a primeira notícia ainda não postada."""
    fontes_embaralhadas = list(FONTES.items())
    random.shuffle(fontes_embaralhadas)

    for nome_fonte, url_rss in fontes_embaralhadas:
        feed = feedparser.parse(url_rss)
        for noticia in feed.entries[:5]:
            if not ja_foi_postada(noticia.link):
                resumo = noticia.get("summary", noticia.get("description", ""))
                return noticia.title, resumo, noticia.link, nome_fonte

    return None, None, None, None


def gerar_imagem_gratis(termo_busca):
    termo_limpo = termo_busca.lower().replace(" ", ",").replace(":", "")
    return f"https://source.unsplash.com/800x400/?{termo_limpo}"


def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    """Reescreve em português (traduzindo se a fonte for internacional), evitando plágio."""

    prompt_texto = f"""
    Você é um jornalista e redator profissional de um blog de notícias em português do Brasil.
    Reescreva a notícia a seguir, no idioma português, mesmo que o conteúdo original esteja em outro idioma.
    REGRAS OBRIGATÓRIAS:
    1. Não copie frases do texto original (mude a estrutura completamente para evitar plágio).
    2. Escreva um texto longo, aprofundado, fluido e bem explicado, em português.
    3. Use apenas tags HTML simples (<p>, <h2>, <strong>, <ul>, <li>).
    4. Não use blocos de código markdown (```html). Retorne apenas o texto com as tags.

    Contexto da notícia original (fonte: {nome_fonte}): {resumo}
    """

    resposta_texto = model.generate_content(prompt_texto)
    conteudo_reescrito = resposta_texto.text

    prompt_titulo = (
        f"Crie, em português, um título inédito, impactante e jornalístico baseado neste tema: "
        f"'{titulo}'. Não use as mesmas palavras do original. Retorne apenas o título."
    )
    novo_titulo = model.generate_content(prompt_titulo).text.strip()

    prompt_tag = (
        f"Com base no título '{titulo}', dê apenas uma palavra em inglês que resuma o assunto "
        f"(ex: technology, sports, economy, politics, war, health). Responda só a palavra."
    )
    palavra_chave = model.generate_content(prompt_tag).text.strip().lower()

    img_url = gerar_imagem_gratis(palavra_chave)

    html_final = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{img_url}" alt="{novo_titulo}" style="max-width:100%; height:auto; border-radius:8px;"/>
    </div>
    {conteudo_reescrito}
    <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
    <p style="font-size: 12px; color: gray; font-style: italic;">
        Com informações adaptadas do portal <a href="{link_fonte}" target="_blank" rel="noopener">{nome_fonte}</a>.
    </p>
    """

    return novo_titulo, html_final


def obter_credenciais():
    """Monta as credenciais a partir do refresh token salvo, sem precisar de navegador."""
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


# --- EXECUÇÃO ---
if __name__ == "__main__":
    tit, resumo, link, fonte = pegar_noticia_multiplas_fontes()
    if tit:
        print(f"📰 Notícia original encontrada no {fonte}: {tit}")
        novo_tit, html_postagem = reescrever_com_ia_anti_plagio(tit, resumo, link, fonte)
        publicar_no_blogger(novo_tit, html_postagem)
        marcar_como_postada(link)
    else:
        print("Nenhuma notícia nova encontrada em nenhuma fonte.")
