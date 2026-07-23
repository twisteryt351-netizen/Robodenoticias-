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

# --- FONTES RSS MESCLADAS ---
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

    # Esportes (Expandido)
    "Globo Esporte": "https://ge.globo.com/rss/",
    "UOL Esporte": "https://rss.uol.com.br/feed/esporte.xml",
    "ESPN Brasil": "https://www.espn.com.br/rss/",
    "Lance!": "https://www.lance.com.br/rss/",
    "Gazeta Esportiva": "https://www.gazetadopovo.com.br/feed/",
    "Trivela": "https://trivela.com.br/feed/",
    "OneFootball (BR)": "https://onefootball.com/feed/br/",
    "TNT Sports BR": "https://tntsports.com.br/feed/",
    "F1 Mania (Automobilismo)": "https://www.f1mania.net/feed/",
    "MMA Fighting / Combate": "https://www.mmafighting.com/rss/index.xml",
    "Superesportes": "https://www.mg.superesportes.com.br/rss/",
    "MKTEsportivo": "https://mktesportivo.com/feed/",

    # Entretenimento, Cultura Pop e Geek
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
    fontes_lista = list(FONTES.items())
    random.shuffle(fontes_lista)
    tentativas = 0
    max_tentativas = 50

    for nome_fonte, url_rss in fontes_lista:
        try:
            feed = feedparser.parse(url_rss, agent="Mozilla/5.0")
        except Exception:
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

def pedir_ia_groq(prompt):
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def gerar_tabela_imagem_blogger(url_img, alt_title, legenda):
    """Gera a estrutura HTML de imagem padrão do Blogger com Tabela Centralizada"""
    return f'''<table align="center" cellpadding="0" cellspacing="0" class="tr-caption-container" style="margin-left: auto; margin-right: auto;"><tbody><tr><td style="text-align: center;"><a href="{url_img}" style="margin-left: auto; margin-right: auto;"><img alt="{alt_title}" border="0" data-original-height="1152" data-original-width="2048" height="360" src="{url_img}" title="{alt_title}" width="640" /></a></td></tr><tr><td class="tr-caption" style="text-align: center;">{legenda}</td></tr></tbody></table><br />'''

def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    imgs = [f"https://picsum.photos/seed/{random.randint(1, 9999)}/2048/1152" for _ in range(3)]

    prompt_titulo = (
        f"Crie um título inédito, sem aspas, chamativo e em português do Brasil para esta notícia: '{titulo}'. "
        f"Responda APENAS com o título em texto puro, sem tags HTML."
    )
    novo_titulo = pedir_ia_groq(prompt_titulo).replace('"', '').replace('\n', ' ').strip()

    img1_html = gerar_tabela_imagem_blogger(imgs[0], novo_titulo, f"Destaque: {novo_titulo}")
    img2_html = gerar_tabela_imagem_blogger(imgs[1], novo_titulo, f"Análise dos fatos principais")
    img3_html = gerar_tabela_imagem_blogger(imgs[2], novo_titulo, f"Desdobramentos e detalhes da notícia")

    caixa_cta_html = '''<div style="background-color: #ffeef4; border-radius: 16px; border: 2px solid rgb(255, 0, 127); box-shadow: rgba(255, 0, 127, 0.15) 0px 4px 20px; color: #2d3748; font-family: sans-serif; margin: 40px 0px; padding: 25px;"><p style="color: #ff007f; font-size: 20px; font-weight: bold; margin-top: 0px; text-align: center;">🎯 Atenção Apaixonado por Notícias e Descontos Exclusivos!</p><p style="font-size: 15px; line-height: 1.6;">Você sabia que existe um <a href="http://s.shopee.com.br/5VQHqQtgyf" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">método revolucionário</a> para economizar de verdade nas suas compras online diariamente? Com os <b>Cupons diários da Shopee</b>, você tem <a href="http://glamourpicklessteward.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">acesso imediato</a> na sua conta a frete grátis, cashback <a href="http://s.shopee.com.br/5fSxez7gvs" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">exclusivo</a> e descontos incríveis!</p><p style="font-size: 15px; line-height: 1.6;">Não perca mais tempo pagando caro. Este é o <a href="http://s.shopee.com.br/5VQHqQtgyf" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">treinamento mais completo</a> para o seu bolso! Acesse todos os dias pelo link oficial e garanta a sua <a href="http://s.shopee.com.br/5VQHqQtgyf" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">transformação definitiva</a> financeira ao <a href="http://glamourpicklessteward.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">resgatar</a> as melhores ofertas antes de todo mundo.</p><p style="font-size: 15px; line-height: 1.6;">Clique <a href="http://glamourpicklessteward.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">abaixo</a> agora mesmo e faça do seu dia a dia de compras uma verdadeira <a href="http://s.shopee.com.br/5fSxez7gvs" style="color: #ff007f; font-weight: bold; text-decoration: underline;" target="_blank">economia</a> inteligente!</p><div style="text-align: center;"><a href="http://s.shopee.com.br/5VQHqQtgyf" style="background-color: #ff007f; border-radius: 12px; box-shadow: rgba(255, 0, 127, 0.3) 0px 4px 10px; color: white; display: inline-block; font-size: 16px; font-weight: bold; margin-top: 15px; padding: 14px 28px; text-align: center; text-decoration: none;" target="_blank">👉 Quero Adquirir Meus Cupons Agora!</a></div></div>'''

    prompt_texto = f"""
    Você é um jornalista e redator SEO profissional de um portal popular.
    Escreva um artigo completo, envolvente e fluído em Português do Brasil com base nas informações fornecidas.

    REGRAS OBRIGATÓRIAS DE FORMATO (HTML PURO):
    1. Retorne APENAS HTML PURO. NUNCA use Markdown (sem **, sem #, sem ```html).
    2. Envolva TODOS os parágrafos nas tags <p> e </p>.
    3. Crie 3 subtítulos usando a tag <h2>Subtítulo Aqui</h2>.
    4. NÃO insira textos soltos como "Nota do autor".

    REGRAS DE DENSIDADE E ESTILO DE LINKS DE AFILIADOS / INTERNOS:
    - Inclua de 4 a 7 links por parágrafo no texto, hiperlinkando em âncoras persuasivas como: "método revolucionário", "jornada transformadora", "segredo do sucesso", "passo a passo definitivo", "oportunidade única", "aprender com especialistas", "transformação definitiva", "conteúdo exclusivo".
    - OBRIGATÓRIO: Aplique o estilo inline exato `style="color: #ff007f; font-weight: bold;" target="_blank"` em TODOS os links.
    - Intercale rigorosamente as seguintes URLs entre as âncoras:
      * [http://s.shopee.com.br/5VQHqQtgyf](http://s.shopee.com.br/5VQHqQtgyf)
      * [http://s.shopee.com.br/5fSxez7gvs](http://s.shopee.com.br/5fSxez7gvs)
      * [http://glamourpicklessteward.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6](http://glamourpicklessteward.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6)
      * [http://glamourpicklessteward.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1](http://glamourpicklessteward.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1)
      * [https://cabinepopnews.blogspot.com/2026/05/a-saga-do-ceu-e-real-o-fim-de-next.html](https://cabinepopnews.blogspot.com/2026/05/a-saga-do-ceu-e-real-o-fim-de-next.html)

    ONDE INSERIR AS IMAGENS SECUNDÁRIAS:
    - Após o primeiro subtítulo <h2>, inclua a marcação: {img2_html}
    - Após o segundo subtítulo <h2>, inclua a marcação: {img3_html}

    Notícia Original capturada ({nome_fonte}):
    Link da fonte: {link_fonte}
    Título: {titulo}
    Resumo: {resumo}
    """

    conteudo_reescrito = pedir_ia_groq(prompt_texto)

    html_final = f"""<p>&nbsp;</p>{img1_html}
{conteudo_reescrito}

{caixa_cta_html}

<hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;" />
<p style="color: #555555; font-size: 13px; font-style: italic; margin-top: 15px;">
    📌 <strong>Fonte da notícia original:</strong> <a href="{link_fonte}" rel="noopener noreferrer" target="_blank">{nome_fonte}</a>
</p>"""

    return novo_titulo, html_final

def obter_credenciais():
    return Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )

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
        print(f"📰 Notícia original capturada de [{fonte}]: {titulo[:100]}...")
        try:
            novo_titulo, html_postagem = reescrever_com_ia_anti_plagio(titulo, resumo, link, fonte)
            print("✍️ Conteúdo formatado e pronto. Publicando no Blogger...")
            publicar_no_blogger(novo_titulo, html_postagem)
            marcar_como_postada(link)
            print("✅ Processo concluído com sucesso!")
        except Exception as e:
            print(f"❌ Erro durante a geração ou publicação: {e}")
    else:
        print("❌ Nenhuma notícia nova disponível no momento.")
