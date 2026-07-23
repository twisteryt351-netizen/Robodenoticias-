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
    imagens = buscar_imagens_openverse(palavra_chave, quantidade=2)
    img_principal, img_secundaria = imagens[0], imagens[1]

    # Gera título novo
    prompt_titulo = (
        f"Crie um título inédito, sem aspas, chamativo e em português do Brasil para esta notícia: '{titulo}'. "
        f"Responda APENAS com o título em texto puro, sem tags HTML."
    )
    novo_titulo = pedir_ia_groq(prompt_titulo).replace('"', '').replace('\n', ' ').strip()

    img1_html = gerar_tabela_imagem_blogger(img_principal, novo_titulo, novo_titulo)
    img2_html = gerar_tabela_imagem_blogger(img_secundaria, novo_titulo, "Entenda os detalhes")

    assunto_leve = eh_assunto_leve(titulo, resumo)

    if assunto_leve:
        instrucao_humor = (
            "5. OBRIGATÓRIO: depois de UM dos subtítulos, insira UMA nota do autor engraçada "
            "dentro de <blockquote>. A piada deve ser natural e relacionada ao tema, como um "
            "comentário de bar. Exemplo: 'Sabe aquela sensação de quando você desiste de comprar "
            "algo caro? O Al-Hilal sentiu isso com Raphinha!'. NÃO repita a piada em outro lugar."
        )
    else:
        instrucao_humor = (
            "5. Este é um assunto sério. NUNCA inclua piadas, brincadeiras ou tom descontraído. "
            "Mantenha respeito e sobriedade do início ao fim."
        )

    # ================================================================
    # PROMPT REFORÇADO COM EXIGÊNCIAS CLARAS
    # ================================================================
    prompt_texto = f"""\
Você é um jornalista de um portal popular do Brasil. Escreva um artigo COMPLETO, APROFUNDADO e com tom CONVERSACIONAL E DESCONTRAÍDO (como se estivesse contando uma história para um amigo).

A notícia é esta:
- Título original: {titulo}
- Resumo: {resumo}
- Fonte: {nome_fonte}

REGRAS OBRIGATÓRIAS (NUNCA DESOBEDEÇA):

1. O artigo deve ter NO MÍNIMO 1200 palavras. 
2. NUNCA repita a mesma informação em parágrafos diferentes. Se você já falou sobre um assunto, vá para outro ângulo.
3. Crie NO MÍNIMO 4 subtítulos com <h2>. Cada subtítulo deve abrir uma nova frente de análise:
   - Exemplo 1: contexto histórico do clube/jogador
   - Exemplo 2: detalhes da negociação (valores, concorrentes)
   - Exemplo 3: reações da torcida e da imprensa
   - Exemplo 4: comparação com outras transferências similares
   - Exemplo 5: o que vem a seguir para o jogador e para o clube
4. Logo após o PRIMEIRO <h2>, insira EXATAMENTE este código: {img2_html}
5. {instrucao_humor}
6. Use uma linguagem natural, com gírias e expressões brasileiras (ex: "bora lá", "segura essa", "pode crer", "é isso aí"). Nada de frases prontas como "é importante lembrar", "é fundamental", "para entender melhor". Seja criativo e autêntico.
7. NÃO invente fatos. Use apenas as informações do resumo, mas pode adicionar contexto histórico/geográfico real que seja relevante.
8. Escreva NO MÍNIMO 8 parágrafos substanciais (cada um com pelo menos 3 frases).
9. Use sinônimos para variar: time/clube/equipe/agremiação, contratação/chegada/negócio/acerto, jogador/atleta/craque.
10. Se o assunto for esporte, cite exemplos de outros clubes ou jogadores para enriquecer a análise.
11. Revise o texto para garantir que NENHUMA frase se repete. Se dois parágrafos começam com a mesma ideia, reescreva um deles.

Agora escreva o artigo completo em HTML puro, com <p> para parágrafos e <h2> para subtítulos. Comece direto, sem introdução genérica.
"""

    conteudo_reescrito = pedir_ia_groq(prompt_texto, temperatura=0.75)

    # ================================================================
    # PÓS-PROCESSAMENTO: REMOVE REPETIÇÕES E FORÇA LINKS
    # ================================================================

    # Lista de links afiliados
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

    # Textos âncora variados para os links (para não repetir)
    ANCHORS = [
        "dá uma olhada aqui",
        "se você curte esse tipo de conteúdo",
        "enquanto isso, no mundo dos negócios",
        "se quiser saber mais sobre o assunto",
        "enquanto você acompanha essa notícia",
        "se você está por dentro do futebol",
        "pra quem gosta de análises aprofundadas",
        "se você quer entender melhor o mercado",
        "enquanto isso, nos bastidores",
        "se você é fã de esportes",
        "pra quem não perde uma notícia",
        "se você quer ficar por dentro",
        "enquanto a bola rola",
        "se você curte futebol e negócios",
        "pra quem acompanha o mercado da bola"
    ]

    def inserir_links_forcados(texto):
        """Insere links em parágrafos que não têm nenhum link."""
        paragrafos = texto.split('</p>')
        novos = []
        links_usados = 0
        max_links = 8
        min_links = 5

        for i, p in enumerate(paragrafos):
            if not p.strip():
                continue

            # Verifica se o parágrafo já tem algum link
            tem_link = 'href="' in p or 'http://' in p or 'https://' in p

            # Se NÃO tem link E ainda não atingimos o máximo de links
            if not tem_link and links_usados < max_links:
                # Escolhe um link aleatório e um âncora aleatório
                link = random.choice(LINKS_AFILIADOS)
                anchor = random.choice(ANCHORS)

                # Remove tags <p> para inserir o link no meio do texto
                conteudo = p.replace('<p>', '').strip()

                # Insere o link em uma posição aleatória (depois do 3º espaço)
                palavras = conteudo.split()
                if len(palavras) > 5:
                    pos = min(random.randint(3, len(palavras)-2), len(palavras)-2)
                    palavras.insert(pos, f'<a href="{link}" target="_blank">{anchor}</a>')
                    novo_conteudo = ' '.join(palavras)
                else:
                    # Se o parágrafo for curto, insere no final
                    novo_conteudo = f'{conteudo} <a href="{link}" target="_blank">{anchor}</a>'

                novo_p = f'<p>{novo_conteudo}</p>'
                novos.append(novo_p)
                links_usados += 1
            else:
                # Mantém o parágrafo original
                if p.startswith('<p>') or p.startswith('<h'):
                    novos.append(p)
                else:
                    novos.append(f'<p>{p}</p>')

        # Se não conseguiu inserir pelo menos 5 links, força nos primeiros parágrafos
        if links_usados < min_links:
            for i in range(min_links - links_usados):
                if i < len(novos):
                    p = novos[i]
                    if '<a href=' not in p:
                        link = random.choice(LINKS_AFILIADOS)
                        anchor = random.choice(ANCHORS)
                        # Insere no final do parágrafo
                        novo_p = p.replace('</p>', f' <a href="{link}" target="_blank">{anchor}</a></p>')
                        novos[i] = novo_p
                        links_usados += 1

        return '</p>'.join(novos) + '</p>' if novos else texto

    # Aplica a inserção forçada de links
    conteudo_reescrito = inserir_links_forcados(conteudo_reescrito)

    # Remove parágrafos muito repetitivos (similaridade > 70%)
    def remover_repetidos(texto):
        paragrafos = re.findall(r'<p>(.*?)</p>', texto, re.DOTALL)
        vistos = []
        resultado = []
        for p in paragrafos:
            p_limpo = re.sub(r'<[^>]+>', '', p).strip().lower()
            if len(p_limpo) < 30:
                resultado.append(f'<p>{p}</p>')
                continue
            repetido = False
            for visto in vistos:
                # Calcula similaridade simples (palavras em comum)
                palavras_p = set(p_limpo.split())
                palavras_v = set(visto.split())
                if len(palavras_p) > 0 and len(palavras_v) > 0:
                    intersecao = len(palavras_p & palavras_v)
                    similaridade = intersecao / max(len(palavras_p), len(palavras_v))
                    if similaridade > 0.65:
                        repetido = True
                        print(f"⚠️ Parágrafo repetido removido: {p_limpo[:50]}...")
                        break
            if not repetido:
                resultado.append(f'<p>{p}</p>')
                vistos.append(p_limpo)
        return '\n'.join(resultado)

    conteudo_reescrito = remover_repetidos(conteudo_reescrito)

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

    caixa_publicidade = (
        '<div style="background-color: #ffeef4; border-radius: 16px; border: 2px solid rgb(255, 0, 127); '
        'box-shadow: rgba(255, 0, 127, 0.15) 0px 4px 20px; color: #2d3748; font-family: sans-serif; '
        'margin: 40px 0px; padding: 25px;">'
        '<p style="color: #ff007f; font-size: 20px; font-weight: bold; margin-top: 0px; text-align: center;">'
        '🎯 Atenção Apaixonado por Notícias e Descontos Exclusivos!</p>'
        '<p style="font-size: 15px; line-height: 1.6;">Você sabia que existe um método revolucionário para '
        'economizar de verdade nas suas compras online diariamente?</p>'
        '</div>'
    )

    html_final = f"""{img1_html}
{conteudo_reescrito}

{caixa_cta}
{caixa_publicidade}
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
