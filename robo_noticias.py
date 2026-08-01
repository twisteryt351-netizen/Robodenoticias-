import os
import urllib.parse
import re
import time
import base64
import random
import requests
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

# Modelo mais capaz do Groq (ainda gratuito), evita repetição e texto raso
MODELO_IA = "llama-3.3-70b-versatile"

# --- GERACAO DE IMAGENS COM IA (Pollinations.ai) ---
# Opcional: se nao configurado, ou se qualquer etapa falhar, o script cai
# automaticamente no metodo antigo (busca de imagem no Openverse).
POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN")  # opcional: remove marca dagua e aumenta limite
# Sem token: 1 requisicao a cada 15s. Com token gratuito (auth.pollinations.ai): a cada 5s.
INTERVALO_POLLINATIONS = 6 if POLLINATIONS_TOKEN else 16
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")
QTD_IMAGENS_NOTICIA = 3

# --- SEU LINK´S DE AFILIADO OBRIGATÓRIO---
# OS LINKS TEM QUE SER DISTRIBUIDOS EM PALAVRAS DE IMPACTO DE 5 A 8 POR PARAGRAFO, randomicamente sem ordem!
# Lista de links separados por vírgula: http://www.effectivecpmnetwork.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6, http://www.effectivecpmnetwork.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1, http://s.shopee.com.br/5VQHqQtgyf, http://www.instagram.com/auracristalencantos, http://solucaodigitalshop.blogspot.com, http://cabinepopnews.blogspot.com, http://s.shopee.com.br/2qTBX58t8P, http://s.shopee.com.br/9zwM4HodQI
# --- FONTES RSS ---
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
    # Luta Livre / WWE
    "WWE Oficial (Notícias)": "https://www.wwe.com/feeds/rss/news",
    "Wrestling Fight Club": "https://wrestlingfightclub.com.br/feed/",
    "Universo Wrestling": "https://universowrestling.com.br/feed/",
    
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
            if feed.bozo and not feed.entries:
                print(f"⚠️ Fonte com problema (sem entradas): {nome_fonte} -> {url_rss}")
                continue
        except Exception as e:
            print(f"⚠️ Fonte falhou ao carregar: {nome_fonte} -> {url_rss} | Erro: {e}")
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


def pedir_ia_groq(prompt, temperatura=0.7):
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODELO_IA,
        temperature=temperatura,
    )
    return response.choices[0].message.content.strip()


def gerar_tabela_imagem_blogger(url_img, alt_title, legenda):
    """Gera a estrutura HTML de imagem padrão do Blogger com legenda centralizada."""
    return f'''<table align="center" cellpadding="0" cellspacing="0" class="tr-caption-container" style="margin-left: auto; margin-right: auto;"><tbody><tr><td style="text-align: center;"><img alt="{alt_title}" border="0" height="360" src="{url_img}" title="{alt_title}" width="640" /></td></tr><tr><td class="tr-caption" style="text-align: center;">{legenda}</td></tr></tbody></table><br />'''


def extrair_palavra_chave(titulo):
    """Pede pra IA uma palavra-chave em inglês que descreva visualmente o assunto real da notícia."""
    prompt_tag = (
        f"Baseado neste título de notícia: '{titulo}', dê apenas UMA palavra-chave em inglês "
        f"que descreva visualmente o assunto principal, para buscar uma foto relacionada "
        f"(ex: 'earthquake', 'football', 'smartphone', 'election', 'hospital', 'comics'). "
        f"Responda só a palavra, sem explicação."
    )
    return pedir_ia_groq(prompt_tag, temperatura=0.3).strip().lower().split()[0]


def gerar_tags_noticia(titulo, resumo, nome_fonte):
    """Pede a IA de 3 a 5 tags/marcadores em português para categorizar a notícia no Blogger,
    considerando que o blog cobre múltiplos nichos (politica, esportes, famosos, tech, clima etc.)."""
    prompt = f"""
Baseado neste título e resumo de notícia, gere de 3 a 5 tags/marcadores em português do Brasil
para categorizar o post em um blog de notícias que cobre política, esportes, entretenimento,
famosos, tecnologia, internacional e clima.

Título: {titulo}
Resumo: {resumo}
Fonte/seção original: {nome_fonte}

REGRAS:
- Tags curtas (1 a 3 palavras cada), sem hashtag, sem numeração, sem aspas.
- A primeira tag deve ser a categoria/editoria principal do assunto (ex: Esportes, Política,
  Tecnologia, Famosos, Internacional, Clima, Entretenimento).
- As demais tags devem ser específicas do assunto da notícia (nomes de temas, times,
  eventos, area — pode citar nomes próprios aqui, pois são apenas marcadores internos).
- Responda APENAS as tags separadas por vírgula, em uma única linha.
"""
    resposta = pedir_ia_groq(prompt, temperatura=0.3)
    tags = [t.strip(" -\"") for t in resposta.strip().split(",") if t.strip(" -\"")]
    if not tags:
        tags = ["Notícias"]
    return tags[:5]


IMAGEM_PADRAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/News_icon.svg/640px-News_icon.svg.png"


def buscar_imagens_openverse(palavra_chave, quantidade=2):
    """Busca fotos reais e gratuitas no Openverse (sem precisar de chave/cadastro)."""
    try:
        resposta = requests.get(
            "https://api.openverse.org/v1/images/",
            params={
                "q": palavra_chave,
                "license_type": "commercial",
                "page_size": max(quantidade, 3),
                "mature": "false",
            },
            headers={"User-Agent": "RoboNoticias/1.0"},
            timeout=10,
        )
        dados = resposta.json()
        resultados = dados.get("results", [])
        urls = [item["url"] for item in resultados if item.get("url")][:quantidade]
        if not urls:
            return [IMAGEM_PADRAO] * quantidade
        while len(urls) < quantidade:
            urls.append(urls[0])
        return urls
    except Exception as e:
        print(f"⚠️ Erro ao buscar imagem no Openverse: {e}")
        return [IMAGEM_PADRAO] * quantidade


DIMENSOES_RATIO = {
    "16:9": (1280, 720),
    "1:1": (1024, 1024),
    "9:16": (720, 1280),
}


def gerar_imagem_pollinations(prompt, ratio="16:9"):
    """Gera uma imagem via Pollinations.ai (gratuito, sem chave, sem cota diaria).
    Retorna bytes da imagem ou None se falhar."""
    largura, altura = DIMENSOES_RATIO.get(ratio, (1280, 720))
    try:
        prompt_codificado = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{prompt_codificado}"
        params = {
            "width": largura,
            "height": altura,
            "model": "flux",
            "seed": random.randint(1, 999999),
            "nologo": "true",
        }
        headers = {}
        if POLLINATIONS_TOKEN:
            headers["Authorization"] = f"Bearer {POLLINATIONS_TOKEN}"
        resposta = requests.get(url, params=params, headers=headers, timeout=120)
        resposta.raise_for_status()
        content_type = resposta.headers.get("Content-Type", "")
        if "image" not in content_type:
            raise ValueError(f"Resposta nao parece ser uma imagem (Content-Type: {content_type})")
        return resposta.content
    except Exception as e:
        print(f"⚠️ Pollinations.ai falhou para o prompt '{prompt[:40]}...': {e}")
        return None


def hospedar_imagem(imagem_bytes, nome_arquivo="imagem.png"):
    """Sobe a imagem gerada para o imgbb.com (host gratuito via API) e retorna a URL publica.
    Catbox.moe bloqueia uploads vindos de IPs de datacenter (ex: GitHub Actions), por isso
    usamos o imgbb, que aceita chamadas de API normalmente."""
    if not IMGBB_API_KEY:
        print("⚠️ Falha ao hospedar imagem: IMGBB_API_KEY nao configurada")
        return None
    try:
        b64 = base64.b64encode(imagem_bytes).decode("utf-8")
        resposta = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": b64, "name": nome_arquivo},
            timeout=30,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        if dados.get("success"):
            return dados["data"]["url"]
        raise ValueError(f"Resposta inesperada do imgbb: {dados}")
    except Exception as e:
        print(f"⚠️ Falha ao hospedar imagem gerada: {e}")
        return None


def gerar_imagem_ia(prompt, ratio="16:9"):
    """Pipeline completo: gera a imagem no Pollinations.ai e hospeda no imgbb. Retorna URL ou None."""
    imagem_bytes = gerar_imagem_pollinations(prompt, ratio)
    if not imagem_bytes:
        return None
    return hospedar_imagem(imagem_bytes)


def gerar_prompts_imagens_noticia(titulo, resumo):
    """Pede a IA 3 prompts de imagem em ingles: capa/thumbnail (para cliques), detalhes
    da noticia, e impactos/repercussao - na mesma ordem em que sao usadas no post."""
    prompt = f"""
Voce e um diretor de arte criando prompts para um gerador de imagens por IA (estilo Stable Diffusion/Flux)
para ilustrar uma materia jornalistica.

Titulo da noticia: "{titulo}"
Resumo: {resumo}

Preciso de exatamente 3 prompts de imagem em INGLES, cada um em uma linha separada, SEM numeracao,
SEM aspas, SEM explicacoes - apenas os prompts, um por linha, nesta ordem:

1) Imagem de CAPA/THUMBNAIL jornalistica: alto impacto visual, composicao central, estilo foto
   editorial/fotojornalismo profissional, iluminacao realista, sem texto escrito na imagem,
   pensada para maximizar cliques mantendo credibilidade jornalistica.
2) Imagem que ilustra os DETALHES da noticia (o fato em si, o cenario onde aconteceu).
3) Imagem que ilustra IMPACTOS E REPERCUSSAO do fato (consequencias, reacoes, desdobramentos).

Cada prompt: descritivo, realista, rico em detalhes visuais (cenario, iluminacao, composicao),
estilo foto jornalistica (nao ilustracao/desenho), SEM citar nomes proprios de pessoas reais,
marcas registradas ou personagens - descreva visualmente sem citar nomes proprios especificos.
Responda APENAS com as 3 linhas de prompt.
"""
    resposta = pedir_ia_groq(prompt, temperatura=0.7)
    linhas = [l.strip(" -\"") for l in resposta.strip().splitlines() if l.strip()]
    while len(linhas) < 3:
        linhas.append(linhas[-1] if linhas else titulo)
    return linhas[:3]


def eh_assunto_leve(titulo, resumo):
    """Pergunta pra IA se o tema permite humor, ou se é sério demais pra brincadeira."""
    prompt = f"""
    Analise este título e resumo de notícia:
    Título: {titulo}
    Resumo: {resumo}

    Este assunto é LEVE (entretenimento, esportes, celebridades, curiosidades, tecnologia,
    cultura pop) ou é SÉRIO (morte, guerra, conflito armado, ataque, tragédia, acidente,
    doença grave, crise humanitária, desastre, crime violento, luto)?

    Responda com APENAS uma palavra: LEVE ou SERIO.
    """
    resposta = pedir_ia_groq(prompt, temperatura=0.1).strip().upper()
    return "LEVE" in resposta


def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    print("🔧 FUNÇÃO REESCREVER COM IA - VERSÃO DEFINITIVA")
    
    try:
        if not IMGBB_API_KEY:
            raise RuntimeError("IMGBB_API_KEY nao configurada")
        prompts_imagens = gerar_prompts_imagens_noticia(titulo, resumo)
        urls_ia = []
        for i, prompt_img in enumerate(prompts_imagens):
            url_img = gerar_imagem_ia(prompt_img, ratio="16:9")
            if not url_img:
                raise RuntimeError(f"Falha ao gerar/hospedar imagem {i + 1}/{QTD_IMAGENS_NOTICIA}")
            urls_ia.append(url_img)
            if i < len(prompts_imagens) - 1:
                time.sleep(INTERVALO_POLLINATIONS)  # respeita o rate limit do Pollinations.ai
        img_principal, img_secundaria, img_terciaria = urls_ia
        print(f"🎨 {len(urls_ia)} imagens geradas via Pollinations.ai.")
    except Exception as e:
        print(f"⚠️ Geracao de imagens via IA falhou, usando metodo padrao (Openverse): {e}")
        palavra_chave = extrair_palavra_chave(titulo)
        print(f"🔑 Palavra-chave: {palavra_chave}")
        imagens = buscar_imagens_openverse(palavra_chave, quantidade=3)
        print(f"🖼️ {len(imagens)} imagens obtidas")
        img_principal, img_secundaria, img_terciaria = imagens[0], imagens[1], imagens[2]

    # Título novo
    prompt_titulo = (
        f"Crie um título inédito, sem aspas, chamativo e em português do Brasil para esta notícia: '{titulo}'. "
        f"Responda APENAS com o título em texto puro, sem tags HTML."
    )
    novo_titulo = pedir_ia_groq(prompt_titulo).replace('"', '').replace('\n', ' ').strip()
    print(f"📌 Novo título: {novo_titulo[:60]}...")

    # Tags/marcadores do post
    tags_post = gerar_tags_noticia(titulo, resumo, nome_fonte)
    print(f"🏷️ Tags geradas: {tags_post}")

    # Meta tags SEO
    prompt_seo = f"""
    Baseado no título e resumo abaixo, gere duas tags meta:
    1. meta description: uma frase curta (máx. 160 caracteres) que resuma a notícia de forma atrativa.
    2. meta keywords: até 10 palavras-chave separadas por vírgula.

    Título: {titulo}
    Resumo: {resumo}

    Responda EXATAMENTE neste formato:
    DESC: [descrição]
    KEYS: [palavras-chave]
    """
    resposta_seo = pedir_ia_groq(prompt_seo, temperatura=0.3)
    descricao = ""
    keywords = ""
    for linha in resposta_seo.splitlines():
        if linha.startswith("DESC:"):
            descricao = linha.replace("DESC:", "").strip()
        elif linha.startswith("KEYS:"):
            keywords = linha.replace("KEYS:", "").strip()
    if not descricao:
        descricao = f"{novo_titulo[:150]} - Fique por dentro dos detalhes."
    if not keywords:
        keywords = "notícias, atualidades, brasil, mundo, política, esportes, entretenimento"

    meta_tags = f"""<!-- SEO Meta -->
<meta name="description" content="{descricao}" />
<meta name="keywords" content="{keywords}" />
<!-- Fim SEO Meta -->"""

    img1_html = gerar_tabela_imagem_blogger(img_principal, novo_titulo, novo_titulo)
    img2_html = gerar_tabela_imagem_blogger(img_secundaria, novo_titulo, "Entenda os detalhes")
    img3_html = gerar_tabela_imagem_blogger(img_terciaria, novo_titulo, "Impactos e repercussões")

    assunto_leve = eh_assunto_leve(titulo, resumo)
    print(f"🎭 Assunto leve: {assunto_leve}")

    # ================================================================
    # PROMPT: GERAR APENAS TEXTO PURO
    # ================================================================
    if assunto_leve:
        tom = "Use linguagem natural e fluida, com um toque pessoal."
    else:
        tom = "Use tom respeitoso e factual."

    prompt_texto = f"""Escreva um artigo jornalístico sobre esta notícia:

TÍTULO: {titulo}
RESUMO: {resumo}

REGRAS:
- {tom}
- Escreva 10 a 12 parágrafos.
- Cada parágrafo deve ter pelo menos 3 frases.
- NUNCA repita a mesma informação.
- Não use títulos, subtítulos, negrito ou qualquer marcação HTML.
- Separe os parágrafos com UMA linha em branco.

Apenas o texto corrido.
"""

    texto_bruto = pedir_ia_groq(prompt_texto, temperatura=0.75)
    print(f"📝 Texto gerado com {len(texto_bruto)} caracteres")

    # ================================================================
    # PASSO 1: DIVIDIR EM PARÁGRAFOS
    # ================================================================
    paragrafos = [p.strip() for p in texto_bruto.split('\n\n') if p.strip()]
    if len(paragrafos) < 4:
        paragrafos = [p.strip() for p in texto_bruto.split('\n') if p.strip()]
    if len(paragrafos) < 4:
        frases = [f.strip() + '.' for f in texto_bruto.split('.') if len(f.strip()) > 20]
        if len(frases) >= 4:
            paragrafos = []
            for i in range(0, len(frases), 3):
                paragrafos.append(' '.join(frases[i:i+3]))
        else:
            paragrafos = [texto_bruto]

    # Remove parágrafos muito curtos e filtra repetidos
    paragrafos = [p for p in paragrafos if len(p) > 30]
    while len(paragrafos) < 8:
        paragrafos.append(paragrafos[-1] if paragrafos else "Contexto adicional sobre o assunto abordado.")

    print(f"📊 {len(paragrafos)} parágrafos extraídos")

    # Remove repetições
    paragrafos_unicos = []
    vistos = []
    for p in paragrafos:
        p_limpo = p.lower()
        if len(p_limpo) < 30:
            paragrafos_unicos.append(p)
            continue
        repetido = False
        for visto in vistos:
            if not visto:
                continue
            palavras_p = set(p_limpo.split())
            palavras_v = set(visto.split())
            if len(palavras_p) == 0 or len(palavras_v) == 0:
                continue
            similaridade = len(palavras_p & palavras_v) / max(len(palavras_p), len(palavras_v))
            if similaridade > 0.5:
                repetido = True
                break
        if not repetido:
            paragrafos_unicos.append(p)
            vistos.append(p_limpo)
    paragrafos = paragrafos_unicos if len(paragrafos_unicos) >= 4 else paragrafos
    print(f"📊 {len(paragrafos)} parágrafos após filtragem")

    # ================================================================
    # PASSO 2: DISTRIBUIR PARÁGRAFOS ENTRE 4 SEÇÕES
    # ================================================================
    h2_titulos = [
        "Contexto e Histórico",
        "Detalhes da Notícia",
        "Reações e Impactos",
        "O Que Vem a Seguir"
    ]

    num_paragrafos = len(paragrafos)
    base = max(2, num_paragrafos // 4)
    resto = num_paragrafos % 4
    indices_secoes = []
    start = 0
    for i in range(4):
        extra = 1 if i < resto else 0
        end = start + base + extra
        indices_secoes.append((start, min(end, num_paragrafos)))
        start = end

    # ================================================================
    # PASSO 3: CONSTRUIR HTML
    # ================================================================
    blocos = []
    
    for i, (inicio, fim) in enumerate(indices_secoes):
        # H2
        blocos.append(f"<h2>{h2_titulos[i]}</h2>")
        print(f"   ➤ Adicionado H2: {h2_titulos[i]}")
        
        # Nota do autor APÓS O PRIMEIRO H2 (se assunto leve)
        if i == 0 and assunto_leve:
            notas = [
                "<blockquote>É impressionante como as notícias mudam rápido, né? Um dia você está acompanhando de um jeito, no outro tudo se transforma. Vida que segue!</blockquote>",
                "<blockquote>Dá pra imaginar a reação das pessoas quando souberam disso. Deve ter sido um misto de choque e curiosidade. O mundo dá voltas, não é mesmo?</blockquote>",
                "<blockquote>Enquanto isso, a gente aqui acompanhando os desdobramentos. Bora ver no que vai dar, porque essa história ainda tem capítulos!</blockquote>"
            ]
            blocos.append(random.choice(notas))
            print("   ➤ Nota do autor inserida")
        
        # Imagem secundária APÓS O PRIMEIRO H2
        if i == 0:
            blocos.append(img2_html)
            print("   ➤ Imagem secundária inserida")
        
        # Parágrafos
        for p in paragrafos[inicio:fim]:
            if p.strip():
                p_limpo = re.sub(r'<[^>]+>', '', p).strip()
                if len(p_limpo) > 20:
                    blocos.append(f"<p>{p_limpo}</p>")
        
        # Imagem terciária APÓS O TERCEIRO H2
        if i == 2:
            blocos.append(img3_html)
            print("   ➤ Imagem terciária inserida")

    conteudo_reescrito = '\n'.join(blocos)
    print(f"📄 HTML montado com {len(blocos)} blocos")

    # ================================================================
    # PASSO 4: INSERIR LINKS DE AFILIADO (90% dos parágrafos)
    # ================================================================
    LINKS_AFILIADOS = [
        "http://www.effectivecpmnetwork.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6",
        "http://www.effectivecpmnetwork.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1",
        "http://s.shopee.com.br/5VQHqQtgyf",
        "http://www.instagram.com/auracristalencantos",
        "http://solucaodigitalshop.blogspot.com",
        "http://cabinepopnews.blogspot.com",
        "http://s.shopee.com.br/2qTBX58t8P",
        "http://s.shopee.com.br/9zwM4HodQI"
    ]

    # Palavras de impacto variadas
    ANCHORS = [
        "confira os detalhes completos", "entenda os bastidores da negociação",
        "veja como isso afeta o mercado", "acompanhe as atualizações em tempo real",
        "descubra o que está por trás da decisão", "saiba o que realmente está em jogo",
        "veja a análise aprofundada", "entenda as implicações para o futuro",
        "confira os próximos passos", "veja o panorama completo da situação",
        "saiba como isso impacta a economia", "entenda o contexto por trás da medida",
        "veja os números e dados relevantes", "confira a visão dos especialistas",
        "saiba mais sobre essa negociação", "veja como isso se desenrola nos próximos dias",
        "entenda as consequências práticas", "confira o que está por vir"
    ]

    def inserir_links_com_palavras_impacto(texto, densidade=0.9):
        paragrafos = re.findall(r'<p>(.*?)</p>', texto, re.DOTALL)
        if not paragrafos:
            return texto

        novos = []
        links_inseridos = 0
        for p in paragrafos:
            if len(p) < 60:
                novos.append(f'<p>{p}</p>')
                continue

            if random.random() < densidade:
                link = random.choice(LINKS_AFILIADOS)
                anchor = random.choice(ANCHORS)
                palavras = p.split()
                if len(palavras) > 6:
                    pos = random.randint(2, len(palavras)-2)
                    palavras.insert(pos, f'<a href="{link}" target="_blank">{anchor}</a>')
                    novo_p = ' '.join(palavras)
                else:
                    novo_p = p + f' <a href="{link}" target="_blank">{anchor}</a>'
                novos.append(f'<p>{novo_p}</p>')
                links_inseridos += 1
            else:
                novos.append(f'<p>{p}</p>')
        
        print(f"🔗 {links_inseridos} links de afiliado inseridos em {len(paragrafos)} parágrafos")
        return '\n'.join(novos)

    conteudo_reescrito = inserir_links_com_palavras_impacto(conteudo_reescrito, densidade=0.9)

    # ================================================================
    # PASSO 5: CORREÇÕES FINAIS
    # ================================================================
    conteudo_reescrito = re.sub(r'(<h2>.*?</h2>)\s*<h2>', r'\1', conteudo_reescrito)
    conteudo_reescrito = re.sub(r'<p>\s*<h2>', '<h2>', conteudo_reescrito)
    conteudo_reescrito = re.sub(r'</h2>\s*</p>', '</h2>', conteudo_reescrito)
    conteudo_reescrito = re.sub(r'<p>\s*</p>', '', conteudo_reescrito)

    # ================================================================
    # MONTAGEM FINAL
    # ================================================================
    caixa_cta = """<div style="background-color: #f4f6f8; border-radius: 12px; margin: 30px 0; padding: 25px; text-align: center; font-family: sans-serif;">
<p style="font-size: 17px; font-weight: bold; color: #333; margin: 0 0 10px 0;">Gostou desta matéria?</p>
<p style="font-size: 14px; color: #555; margin: 0 0 15px 0;">Deixe seu comentário abaixo e compartilhe com quem também acompanha esse assunto!</p>
<div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
    <a href="#" onclick="window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(document.title + ' - ' + window.location.href), '_blank'); return false;" style="background-color: #25d366; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">🟢 WhatsApp</a>
    <a href="#" onclick="window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(window.location.href), '_blank'); return false;" style="background-color: #1877f2; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">🔵 Facebook</a>
    <a href="#" onclick="window.open('https://twitter.com/intent/tweet?url=' + encodeURIComponent(window.location.href), '_blank'); return false;" style="background-color: #000; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">⚫ X</a>
</div>
</div>
"""

    html_final = f"""{meta_tags}

{img1_html}
{conteudo_reescrito}

{caixa_cta}
<hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;" />
<p style="color: #555555; font-size: 13px; font-style: italic; margin-top: 15px;">
    📌 <strong>Fonte da notícia original:</strong> <a href="{link_fonte}" rel="noopener noreferrer" target="_blank">{nome_fonte}</a>
</p>"""

    print("✅ Função reescrever_com_ia_anti_plagio finalizada")
    return novo_titulo, html_final, tags_post
def obter_credenciais():
    return Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
def publicar_no_blogger(titulo, conteudo, tags=None):
    creds = obter_credenciais()
    blogger = build('blogger', 'v3', credentials=creds)

    corpo_postagem = {
        'kind': 'blogger#post',
        'title': titulo,
        'content': conteudo
    }
    if tags:
        corpo_postagem['labels'] = tags

    resultado = blogger.posts().insert(blogId=BLOGGER_ID, body=corpo_postagem).execute()
    print(f"🔥 Sucesso! Post criado: '{titulo}' -> {resultado.get('url')}")


if __name__ == "__main__":
    print("🚀 Iniciando busca por notícia inédita...")
    titulo, resumo, link, fonte = pegar_noticia_multiplas_fontes()

    if titulo:
        print(f"📰 Notícia original capturada de [{fonte}]: {titulo[:100]}...")
        try:
            novo_titulo, html_postagem, tags_post = reescrever_com_ia_anti_plagio(titulo, resumo, link, fonte)
            print("✍️ Conteúdo formatado e pronto. Publicando no Blogger...")
            publicar_no_blogger(novo_titulo, html_postagem, tags_post)
            marcar_como_postada(link)
            print("✅ Processo concluído com sucesso!")
        except Exception as e:
            print(f"❌ Erro durante a geração ou publicação: {e}")
    else:
        print("❌ Nenhuma notícia nova disponível no momento.")
