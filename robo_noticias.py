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
    # --- Portais de Notícias Gerais ---
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

    # --- Jornais e Revistas ---
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

    # --- Esportes ---
    "Globo Esporte": "https://ge.globo.com/rss/",
    "UOL Esporte": "https://rss.uol.com.br/feed/esporte.xml",
    "ESPN Brasil": "https://www.espn.com.br/rss/",
    "Lance!": "https://www.lance.com.br/rss/",
    "Gazeta Esportiva": "https://www.gazetaesportiva.com/feed/",
    "Trivela": "https://trivela.com.br/feed/",
    "OneFootball (BR)": "https://onefootball.com/feed/br/",
    "TNT Sports BR": "https://tntsports.com.br/feed/",

    # --- Entretenimento, Cultura Pop e Geek ---
    "Omelete": "https://www.omelete.com.br/sitemap-news.xml",
    "Jovem Nerd": "https://jovemnerd.com.br/feed-completo",
    "Critical Hits": "https://criticalhits.com.br/feed/",
    "Legião dos Heróis": "https://legiaodosherois.com.br/feed/",
    "IGN Brasil": "https://br.ign.com/feed/",
    "TecMundo": "https://tecmundo.com.br/feed/",
    "Canaltech": "https://canaltech.com.br/feed/",
    "AdoroCinema": "https://www.adorocinema.com.br/rss/",
    "Combo Infinito": "https://comboinfinito.com.br/feed/",
    "The Enemy": "https://theenemy.com.br/feed/",
    "Garotas Geeks": "https://garotasgeeks.com/feed/",

    # --- Fofocas e Celebridades ---
    "Quem Acontece": "https://quem.globo.com/rss/",
    "Contigo!": "https://contigo.com.br/feed/",
    "Caras": "https://caras.com.br/feed/",
    "OFuxico": "https://ofuxico.com.br/feed/",
    "Purepeople BR": "https://www.purepeople.com.br/rss.xml",

    # --- Internacional ---
    "BBC News (Mundo)": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "CNN Internacional": "http://rss.cnn.com/rss/edition.rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "El País Brasil": "https://elpais.com/arc/outboundfeeds/rss/tags_slug/brasil-a/?outputType=xml",
    "France 24 Português": "https://www.france24.com/pt/rss",

    # --- Clima e Previsão do Tempo ---
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
    1. Não copie frases do texto original (mude a estrutura completamente para evitar plágio). Persona seria estilo conversacional, informativo e descontraido. 
    2. Escreva um texto longo, aprofundado, fluido e bem explicado, em português.
    3. Use apenas tags HTML simples (<p>, <h2>, <strong>, <ul>, <li>).
    4. Não use blocos de código markdown (```html). Retorne apenas o texto com as tags.
    5. Titulo matador Seo, para aparecer nas primeiras paginas do google
    6. Artigos todos estruturados de 1500+ palavras minimo, seo aplicado, titulo e subtitulos matadores, chamada para ação no final, compartilhar, comentar e etc...
    7. 5 palavras de impacto por paragrafo escondera links, assim se o leitor clicar vai para o site de afiliado... Os links:  http://www.effectivecpmnetwork.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6, http://www.effectivecpmnetwork.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1, http://s.shopee.com.br/5VQHqQtgyf, http://www.instagram.com/auracristalencantos, http://solucaodigitalshop.blogspot.com, http://cabinepopnews.blogspot.com, http://s.shopee.com.br/2qTBX58t8P, http://s.shopee.com.br/9zwM4HodQI,  
    8. Espalhe 4 notas do autor com caracter engraçado, ou ironico dependendo do post ele dá sentido, estas notas tem que está espalhados pelo post. 
    9. Não esquece de citar as fontes, seja no inicio ou no final, deixa claro que não disseminamos fakenews, se quiser poste o link da noticia real para salva guardar a integridade do post!
    10. Revise tudo com rigor para não fugir a nenhuma regra!

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
