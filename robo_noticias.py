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

# --- FONTES RSS MESCLADAS (COM ESPORTES EXPANDIDO) ---
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

def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    # Genera 4 imagens com seeds aleatórios
    imgs = [f"https://picsum.photos/seed/{random.randint(1, 9999)}/800/400" for _ in range(4)]

    # 1. Gera o título inédito
    prompt_titulo = (
        f"Crie um título inédito, sem aspas, chamativo e em português do Brasil para esta notícia: '{titulo}'. "
        f"Responda APENAS com o título em texto puro, sem tags HTML."
    )
    novo_titulo = pedir_ia_groq(prompt_titulo).replace('"', '').replace('\n', ' ').strip()

    # Textos de SEO para as 4 imagens
    alts = [
        f"{novo_titulo} - Imagem principal da notícia",
        f"Detalhes sobre {novo_titulo}",
        f"Análise do impacto sobre {novo_titulo}",
        f"Informações adicionais - {novo_titulo}"
    ]
    
    titles = [
        f"Capa: {novo_titulo}",
        f"Ilustração 1 - {novo_titulo}",
        f"Ilustração 2 - {novo_titulo}",
        f"Conclusão - {novo_titulo}"
    ]

    # Estruturas HTML das 4 imagens
    img1_html = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{imgs[0]}" alt="{alts[0]}" title="{titles[0]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'
    img2_html = f'<div style="text-align: center; margin: 25px 0;"><img src="{imgs[1]}" alt="{alts[1]}" title="{titles[1]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'
    img3_html = f'<div style="text-align: center; margin: 25px 0;"><img src="{imgs[2]}" alt="{alts[2]}" title="{titles[2]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'
    img4_html = f'<div style="text-align: center; margin: 25px 0;"><img src="{imgs[3]}" alt="{alts[3]}" title="{titles[3]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'

    # 2. Gera o corpo do artigo
    prompt_texto = f"""
    Você é um jornalista de um portal popular no Brasil. 
    Escreva um artigo de notícia completo, descontraído e fluido em Português do Brasil com base nas informações fornecidas.

    REGRAS OBRIGATÓRIAS DE FORMATO (HTML PURO):
    1. Retorne APENAS HTML PURO. NUNCA use Markdown (sem **, sem #, sem listas soltas).
    2. TODOS os parágrafos sem exceção DEVEM estar envolvidos nas tags <p> e </p>.
    3. Crie 3 subtítulos usando a tag <h2>Subtítulo aqui</h2>.
    4. Crie 3 notas do autor usando a tag <p><em>(Nota do autor: ...)</em></p>.

    REGRAS PARA AS IMAGENS DO MEIO DO TEXTO:
    No meio do artigo (entre os parágrafos e subtítulos), você DEVE obrigatoriamente colar as 3 tags de imagem abaixo exatamente como fornecidas:
    {img2_html}
    {img3_html}
    {img4_html}

    REGRAS DOS LINKS DE AFILIADO (DILUÍDOS NATURALMENTE NO TEXTO):
    Não coloque os links no final! Insira-os naturalmente DENTRO das frases ao longo dos parágrafos:
    - ...para economizar no dia a dia, <a href="http://s.shopee.com.br/5VQHqQtgyf" target="_blank">confira esta seleção especial</a> de ofertas.
    - ...para ficar por dentro de tudo, <a href="http://cabinepopnews.blogspot.com" target="_blank">acesse mais notícias exclusivas</a> no blog.
    - ...se você busca soluções práticas, <a href="http://solucaodigitalshop.blogspot.com" target="_blank">veja as novidades aqui</a> na loja.
    - ...aproveite também para conferir e <a href="http://s.shopee.com.br/2qTBX58t8P" target="_blank">garantir descontos agora</a> nas promoções.

    Notícia Original ({nome_fonte}):
    Título: {titulo}
    Resumo: {resumo}
    """

    conteudo_reescrito = pedir_ia_groq(prompt_texto)

    # Montagem do HTML final garantindo a referência da fonte original no rodapé
    html_final = f"""
    {img1_html}
    {conteudo_reescrito}
    <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
    <p style="font-size: 13px; color: #555; font-style: italic; margin-top: 15px;">
        📌 <strong>Fonte da notícia original:</strong> <a href="{link_fonte}" target="_blank" rel="noopener noreferrer">{nome_fonte}</a>
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
