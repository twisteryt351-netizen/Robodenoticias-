import os
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


import re
import random

def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    palavra_chave = extrair_palavra_chave(titulo)
    imagens = buscar_imagens_openverse(palavra_chave, quantidade=3)
    img_principal, img_secundaria, img_terciaria = imagens[0], imagens[1], imagens[2]

    # Gera título novo
    prompt_titulo = (
        f"Crie um título inédito, sem aspas, chamativo e em português do Brasil para esta notícia: '{titulo}'. "
        f"Responda APENAS com o título em texto puro, sem tags HTML."
    )
    novo_titulo = pedir_ia_groq(prompt_titulo).replace('"', '').replace('\n', ' ').strip()

    # Gera meta tags SEO
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

    # ================================================================
    # PROMPT CURTO E OBJETIVO
    # ================================================================
    prompt_texto = f"""Escreva um artigo sobre esta notícia:

Título: {titulo}
Resumo: {resumo}

REGRAS:
- Use 4 subtítulos com <h2>.
- {">"}Se for assunto leve, insira 1 nota do autor em <blockquote> após o primeiro <h2>.
- Escreva 10 parágrafos com <p>.
- Não repita informações.
- Use linguagem natural, sem exageros.

Comece direto com o HTML.
"""

    conteudo_reescrito = pedir_ia_groq(prompt_texto, temperatura=0.75)

    # ================================================================
    # PASSO 1: GARANTIR 4 SUBTÍTULOS H2
    # ================================================================
    # Conta quantos H2 existem
    h2_count = len(re.findall(r'<h2>', conteudo_reescrito))
    
    if h2_count < 4:
        # Títulos padrão para injetar
        h2_padrao = [
            "<h2>Contexto e Histórico</h2>",
            "<h2>Detalhes da Notícia</h2>",
            "<h2>Reações e Impactos</h2>",
            "<h2>O Que Vem a Seguir</h2>"
        ]
        
        # Remove H2 existentes para evitar duplicação
        conteudo_reescrito = re.sub(r'<h2>.*?</h2>', '', conteudo_reescrito)
        
        # Insere os 4 H2 antes de cada grupo de parágrafos
        paragrafos = re.findall(r'<p>.*?</p>', conteudo_reescrito, re.DOTALL)
        if len(paragrafos) >= 4:
            # Distribui os H2 entre os parágrafos
            novo_conteudo = ""
            for i, h2 in enumerate(h2_padrao):
                # Pega um bloco de parágrafos (cerca de 2-3 por seção)
                inicio = i * (len(paragrafos) // 4)
                fim = (i + 1) * (len(paragrafos) // 4) if i < 3 else len(paragrafos)
                bloco = ''.join(paragrafos[inicio:fim])
                novo_conteudo += h2 + '\n' + bloco
            conteudo_reescrito = novo_conteudo
        else:
            # Se tiver poucos parágrafos, insere todos os H2 no início
            conteudo_reescrito = '\n'.join(h2_padrao) + '\n' + conteudo_reescrito
        
        print(f"⚠️ {4 - h2_count} subtítulos H2 foram injetados.")

    # ================================================================
    # PASSO 2: GARANTIR NOTA DO AUTOR (se assunto leve)
    # ================================================================
    if assunto_leve and '<blockquote>' not in conteudo_reescrito:
        notas = [
            "<blockquote>E olha que essa notícia pegou todo mundo de surpresa! Quem diria que ia dar nisso, né?</blockquote>",
            "<blockquote>Dá pra imaginar a reação das pessoas quando souberam disso. Deve ter sido um misto de choque e curiosidade.</blockquote>",
            "<blockquote>Enquanto isso, a gente aqui acompanhando os desdobramentos. Bora ver no que vai dar!</blockquote>"
        ]
        nota = random.choice(notas)
        
        # Insere após o primeiro </h2>
        if '</h2>' in conteudo_reescrito:
            partes = conteudo_reescrito.split('</h2>', 1)
            conteudo_reescrito = partes[0] + '</h2>\n' + nota + '\n' + partes[1]
        else:
            # Fallback: insere no início
            conteudo_reescrito = nota + '\n' + conteudo_reescrito
        print("✅ Nota do autor injetada.")

    # ================================================================
    # PASSO 3: INSERIR 3 IMAGENS
    # ================================================================
    # Imagem 1: já está no topo (img1_html)
    # Imagem 2: insere após o primeiro H2
    if '<h2>' in conteudo_reescrito:
        partes = conteudo_reescrito.split('<h2>', 1)
        if len(partes) == 2:
            conteudo_reescrito = partes[0] + '<h2>' + partes[1].replace('</h2>', '</h2>\n' + img2_html, 1)
    
    # Imagem 3: insere após o terceiro H2 ou no meio do texto
    h2_positions = [m.start() for m in re.finditer(r'<h2>', conteudo_reescrito)]
    if len(h2_positions) >= 3:
        # Insere após o terceiro H2
        pos = h2_positions[2]
        # Encontra o fechamento do terceiro H2
        end_pos = conteudo_reescrito.find('</h2>', pos) + 6
        conteudo_reescrito = conteudo_reescrito[:end_pos] + '\n' + img3_html + '\n' + conteudo_reescrito[end_pos:]
    else:
        # Fallback: insere no final
        conteudo_reescrito = conteudo_reescrito + '\n' + img3_html

    # ================================================================
    # PASSO 4: REMOVER REPETIÇÕES
    # ================================================================
    def remover_repetidos(texto):
        paragrafos = re.findall(r'<p>(.*?)</p>', texto, re.DOTALL)
        if not paragrafos:
            return texto

        resultado = []
        vistos = []
        for p in paragrafos:
            p_limpo = re.sub(r'<[^>]+>', '', p).strip().lower()
            if len(p_limpo) < 30:
                resultado.append(f'<p>{p}</p>')
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
                resultado.append(f'<p>{p}</p>')
                vistos.append(p_limpo)
        return '\n'.join(resultado)

    conteudo_reescrito = remover_repetidos(conteudo_reescrito)

    # ================================================================
    # PASSO 5: INSERIR LINKS DE AFILIADO (DENSIDADE ALTA)
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

    ANCHOR_FIXO = "saiba mais"

    def inserir_links_repetidos(texto, densidade=0.7):
        """Insere links em 70% dos parágrafos, repetindo à vontade."""
        paragrafos = re.findall(r'<p>(.*?)</p>', texto, re.DOTALL)
        if not paragrafos:
            return texto

        novos_paragrafos = []
        for p in paragrafos:
            if len(p) < 50:
                novos_paragrafos.append(f'<p>{p}</p>')
                continue

            # Insere link em 70% dos parágrafos
            if random.random() < densidade:
                link = random.choice(LINKS_AFILIADOS)
                palavras = p.split()
                if len(palavras) > 5:
                    pos = random.randint(2, len(palavras)-1)
                    palavras.insert(pos, f'<a href="{link}" target="_blank">{ANCHOR_FIXO}</a>')
                    novo_p = ' '.join(palavras)
                else:
                    novo_p = p + f' <a href="{link}" target="_blank">{ANCHOR_FIXO}</a>'
                novos_paragrafos.append(f'<p>{novo_p}</p>')
            else:
                novos_paragrafos.append(f'<p>{p}</p>')

        return '\n'.join(novos_paragrafos)

    conteudo_reescrito = inserir_links_repetidos(conteudo_reescrito, densidade=0.7)

    # ================================================================
    # PASSO 6: CORREÇÃO DE SUBTÍTULOS DENTRO DE P
    # ================================================================
    conteudo_reescrito = re.sub(r'<p>\s*<h2>', '<h2>', conteudo_reescrito)
    conteudo_reescrito = re.sub(r'</h2>\s*</p>', '</h2>', conteudo_reescrito)

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
