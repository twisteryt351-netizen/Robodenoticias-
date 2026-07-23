import os
import random
import time
import feedparser
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURAÇÕES (variáveis de ambiente) ---
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
model = genai.GenerativeModel('gemini-pro')

# --- FONTES RSS (corrigidas) ---
FONTES = {
    # Portais de Notícias Gerais
    "G1": "https://g1.globo.com/rss/g1/",
    "G1 Tecnologia": "https://g1.globo.com/rss/g1/tecnologia/",
    "UOL Notícias": "https://rss.uol.com.br/feed/noticias.xml",
    "Terra Notícias": "https://terra.com.br/rss/noticias/",
    "R7 Notícias": "https://noticias.r7.com/feed/",
    "Band Notícias": "https://band.com.br/rss/noticias/",
    "Record Notícias": "https://noticias.r7.com/record/feed/",
    "SBT News": "https://sbtnews.sbt.com.br/feed/",
    "Jovem Pan Notícias": "https://jovempan.com.br/feed/",
    "BBC Brasil": "https://www.bbc.com/portuguese/index.xml",

    # Jornais e Revistas
    "Folha de S.Paulo": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
    "O Estado de S.Paulo (Estadão)": "https://www.estadao.com.br/rss/",
    "O Globo": "https://oglobo.globo.com/rss/",
    "Extra": "https://extra.globo.com/rss/",
    "Zero Hora": "https://zerohora.clicrbs.com.br/rss/",
    "Correio Braziliense": "https://www.correiobraziliense.com.br/rss/",
    "Gazeta do Povo": "https://www.gazetadopovo.com.br/feed/",
    "Veja": "https://veja.abril.com.br/feed/",
    "Época": "https://epoca.globo.com/rss/",
    "IstoÉ": "https://istoe.com.br/feed/",

    # Esportes
    "Globo Esporte": "https://ge.globo.com/rss/",
    "UOL Esporte": "https://rss.uol.com.br/feed/esporte.xml",
    "ESPN Brasil": "https://www.espn.com.br/rss/",
    "Lance!": "https://www.lance.com.br/rss/",
    "Gazeta Esportiva": "https://www.gazetaesportiva.com/feed/",
    "Trivela": "https://trivela.com.br/feed/",
    "OneFootball (BR)": "https://onefootball.com/feed/br/",
    "TNT Sports BR": "https://tntsports.com.br/feed/",

    # Entretenimento, Cultura Pop e Geek
    "Omelete": "https://www.omelete.com.br/sitemap-news.xml",
    "Jovem Nerd": "https://jovemnerd.com.br/feed-completo",
    "Critical Hits": "https://criticalhits.com.br/feed/",
    "Legião dos Heróis": "https://legiaodosherois.com.br/feed/",
    "IGN Brasil": "https://br.ign.com/feed/",  # CORRIGIDO
    "TecMundo": "https://tecmundo.com.br/feed/",
    "Canaltech": "https://canaltech.com.br/feed/",
    "AdoroCinema": "https://www.adorocinema.com.br/rss/",
    "Combo Infinito": "https://comboinfinito.com.br/feed/",
    "The Enemy": "https://theenemy.com.br/feed/",
    "Garotas Geeks": "https://garotasgeeks.com/feed/",

    # Fofocas e Celebridades
    "Quem Acontece": "https://quem.globo.com/rss/",
    "Contigo!": "https://contigo.com.br/feed/",
    "Caras": "https://caras.com.br/feed/",
    "OFuxico": "https://ofuxico.com.br/feed/",
    "Purepeople BR": "https://www.purepeople.com.br/rss.xml",

    # Internacional
    "BBC News (Mundo)": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "CNN Internacional": "http://rss.cnn.com/rss/edition.rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "El País Brasil": "https://elpais.com/arc/outboundfeeds/rss/tags_slug/brasil-a/?outputType=xml",
    "France 24 Português": "https://www.france24.com/pt/rss",

    # Clima
    "Climatempo": "https://www.climatempo.com.br/rss/",
    "Metsul Meteorologia": "https://metsul.com/feed/",
    "INMET Notícias": "https://portal.inmet.gov.br/noticias/rss",
    "Tempo.com Meteored": "https://www.tempo.com/rss/",
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
    """
    Tenta encontrar uma notícia inédita.
    Para cada fonte, tenta até 3 notícias.
    Se nenhuma for inédita, passa para a próxima fonte.
    Limita a 50 tentativas no total para não entrar em loop infinito.
    """
    fontes_lista = list(FONTES.items())
    random.shuffle(fontes_lista)
    tentativas = 0
    max_tentativas = 50

    for nome_fonte, url_rss in fontes_lista:
        try:
            feed = feedparser.parse(url_rss, agent="Mozilla/5.0")
        except Exception as e:
            print(f"⚠️ Erro ao parsear {nome_fonte}: {e}")
            continue

        for entrada in feed.entries[:5]:  # pega até 5 notícias
            tentativas += 1
            if tentativas > max_tentativas:
                print("⚠️ Limite de tentativas atingido. Saindo.")
                return None, None, None, None

            link = entrada.get("link")
            titulo = entrada.get("title")
            resumo = entrada.get("summary") or entrada.get("description") or ""

            if not link or not titulo:
                continue

            if not ja_foi_postada(link):
                print(f"✅ Notícia inédita encontrada em {nome_fonte}: {titulo[:60]}...")
                return titulo, resumo, link, nome_fonte

    print("⚠️ Nenhuma notícia nova encontrada em nenhuma fonte.")
    return None, None, None, None

def gerar_imagem_gratis(termo_busca):
    termo_limpo = termo_busca.lower().replace(" ", ",").replace(":", "")
    if not termo_limpo:
        termo_limpo = "news"
    return f"https://source.unsplash.com/800x400/?{termo_limpo}"

def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    """
    Gera conteúdo único usando Gemini.
    """
    # Prompt principal (mantive suas regras)
    prompt_texto = f"""
    Você é um jornalista e redator profissional de um blog de notícias em português do Brasil.
    Reescreva a notícia a seguir, no idioma português, mesmo que o conteúdo original esteja em outro idioma.

    REGRAS OBRIGATÓRIAS:
    1. Não copie frases do texto original (mude a estrutura completamente para evitar plágio). Persona estilo conversacional, informativo e descontraído.
    2. Escreva um texto longo, aprofundado, fluido e bem explicado, em português (mínimo 1500 palavras).
    3. Use apenas tags HTML simples (<p>, <h2>, <strong>, <ul>, <li>).
    4. Não use blocos de código markdown (```html). Retorne apenas o texto com as tags.
    5. Título matador SEO, para aparecer nas primeiras páginas do Google.
    6. Estrutura com subtítulos matadores, chamada para ação no final (compartilhar, comentar etc.).
    7. Espalhe 4 notas do autor com tom engraçado ou irônico (dependendo do post) ao longo do texto.
    8. Insira os seguintes links de afiliado (escondidos em palavras de impacto, como "clique aqui", "saiba mais", "veja agora"):
       - http://www.effectivecpmnetwork.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6
       - http://www.effectivecpmnetwork.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1
       - http://s.shopee.com.br/5VQHqQtgyf
       - http://www.instagram.com/auracristalencantos
       - http://solucaodigitalshop.blogspot.com
       - http://cabinepopnews.blogspot.com
       - http://s.shopee.com.br/2qTBX58t8P
       - http://s.shopee.com.br/9zwM4HodQI
    9. Cite a fonte no início ou no final, deixando claro que não disseminamos fakenews (inclua o link real).
    10. Revise tudo com rigor para não fugir a nenhuma regra.

    Contexto da notícia original (fonte: {nome_fonte}):
    Título: {titulo}
    Resumo: {resumo}
    """

    resposta = model.generate_content(prompt_texto)
    conteudo_reescrito = resposta.text

    if not conteudo_reescrito or len(conteudo_reescrito) < 200:
        raise ValueError("Conteúdo gerado pela IA está vazio ou muito curto.")

    # Gerar novo título
    prompt_titulo = (
        f"Crie, em português, um título inédito, impactante e jornalístico baseado neste tema: "
        f"'{titulo}'. Não use as mesmas palavras do original. Retorne apenas o título."
    )
    novo_titulo = model.generate_content(prompt_titulo).text.strip()
    # Limpeza básica do título
    novo_titulo = novo_titulo.replace("\n", " ").strip()

    # Gerar palavra‑chave para imagem
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

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    print("🚀 Iniciando busca por notícia inédita...")
    titulo, resumo, link, fonte = pegar_noticia_multiplas_fontes()

    if titulo:
        print(f"📰 Notícia original: {titulo[:100]}...")
        try:
            novo_titulo, html_postagem = reescrever_com_ia_anti_plagio(titulo, resumo, link, fonte)
            print("✍️ Conteúdo gerado com sucesso. Publicando...")
            publicar_no_blogger(novo_titulo, html_postagem)
            marcar_como_postada(link)
            print("✅ Processo concluído.")
        except Exception as e:
            print(f"❌ Erro durante a geração ou publicação: {e}")
    else:
        print("❌ Nenhuma notícia nova disponível no momento.")
