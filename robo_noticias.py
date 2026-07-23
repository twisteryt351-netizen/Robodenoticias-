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
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
BLOGGER_ID = os.environ.get("BLOGGER_ID")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

for nome, valor in [
    ("GROQ_API_KEY", GROQ_API_KEY),
    ("PIXABAY_API_KEY", PIXABAY_API_KEY),
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

# --- SEU LINK DE AFILIADO (opcional) ---
# Coloque aqui SEU link de afiliado real e legítimo (ex: Shopee, Amazon Associates, etc).
# Ele vai aparecer em UMA ÚNICA caixa no final do post, claramente identificada como
# "Publicidade" — isso é o que te protege de banimento por link stuffing/cloaking.
LINK_AFILIADO = os.environ.get("LINK_AFILIADO", "")  # deixe vazio se não tiver ainda

# --- FONTES RSS ---
FONTES = {
    # Portais de Notícias Gerais
    "G1": "https://g1.globo.com/rss/g1/",
    "G1 Tecnologia": "https://g1.globo.com/rss/g1/tecnologia/",
    "UOL Notícias": "https://rss.uol.com.br/feed/noticias.xml",
    "R7 Notícias": "https://noticias.r7.com/feed/",
    "BBC Brasil": "https://www.bbc.com/portuguese/index.xml",

    # Jornais e Revistas
    "Folha de S.Paulo": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
    "O Estado de S.Paulo (Estadão)": "https://www.estadao.com.br/rss/",
    "Veja": "https://veja.abril.com.br/feed/",

    # Esportes
    "Globo Esporte": "https://ge.globo.com/rss/",
    "UOL Esporte": "https://rss.uol.com.br/feed/esporte.xml",
    "ESPN Brasil": "https://www.espn.com.br/rss/",
    "Lance!": "https://www.lance.com.br/rss/",

    # Luta Livre / WWE
    "WWE Oficial (Notícias)": "https://www.wwe.com/feeds/rss/news",
    "Wrestling Fight Club": "https://wrestlingfightclub.com.br/feed/",
    "Universo Wrestling": "https://universowrestling.com.br/feed/",

    # Entretenimento, Cultura Pop e Geek
    "Omelete": "https://www.omelete.com.br/sitemap-news.xml",
    "Jovem Nerd": "https://jovemnerd.com.br/feed-completo",
    "TecMundo": "https://tecmundo.com.br/feed/",
    "Canaltech": "https://canaltech.com.br/feed/",

    # Internacional
    "BBC News (Mundo)": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "CNN Internacional": "http://rss.cnn.com/rss/edition.rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",

    # Clima
    "Climatempo": "https://www.climatempo.com.br/rss/",
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


IMAGEM_PADRAO = "https://cdn.pixabay.com/photo/2016/11/29/03/53/news-1867010_1280.jpg"


def buscar_imagens_pixabay(palavra_chave, quantidade=2):
    """Busca fotos reais e gratuitas no Pixabay relacionadas ao tema da notícia."""
    try:
        resposta = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": palavra_chave,
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": max(quantidade, 3),
            },
            timeout=10,
        )
        dados = resposta.json()
        hits = dados.get("hits", [])
        urls = [item["largeImageURL"] for item in hits[:quantidade]]
        if not urls:
            return [IMAGEM_PADRAO] * quantidade
        # Se só achou 1 imagem, repete pra preencher
        while len(urls) < quantidade:
            urls.append(urls[0])
        return urls
    except Exception as e:
        print(f"⚠️ Erro ao buscar imagem no Pixabay: {e}")
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


def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    palavra_chave = extrair_palavra_chave(titulo)
    imagens = buscar_imagens_pixabay(palavra_chave, quantidade=2)
    img_principal, img_secundaria = imagens[0], imagens[1]

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
            "5. Depois de um dos subtítulos, insira UMA (só uma) nota do autor leve e "
            "engraçada dentro de uma tag <blockquote>, como um comentário pessoal e "
            "descontraído do redator. Não exagere, e não repita a piada em outro lugar."
        )
    else:
        instrucao_humor = (
            "5. Este é um assunto sério. NÃO inclua nenhuma piada, brincadeira ou comentário "
            "descontraído. Mantenha um tom respeitoso, factual e sóbrio do início ao fim."
        )

    prompt_texto = f"""
    Você é um jornalista e redator profissional de um portal de notícias popular no Brasil.
    Escreva um artigo completo, envolvente e fluido em português, com base nas informações reais abaixo.
    NÃO repita a mesma frase ou ideia mais de uma vez. Cada parágrafo deve trazer informação nova.

    REGRAS DE FORMATO (HTML PURO):
    1. Retorne APENAS HTML puro. NUNCA use Markdown (sem **, sem #, sem ```html).
    2. Envolva todos os parágrafos em tags <p>.
    3. Crie 2 subtítulos usando a tag <h2>.
    4. Logo após o primeiro <h2>, insira exatamente este trecho: {img2_html}
    {instrucao_humor}
    6. Não insira nenhum link dentro do corpo do texto. Nenhum. O texto deve ser 100%
       informativo, sem links de afiliado, sem "clique aqui", sem chamadas de venda.
    7. NÃO invente fatos, números ou declarações que não estejam no resumo fornecido.
    8. Escreva pelo menos 4 parágrafos substanciais, cada um trazendo um ângulo diferente
       da notícia (contexto, detalhes, repercussão, próximos passos) — nunca reafirmando
       o que já foi dito.

    Notícia original capturada (fonte: {nome_fonte}):
    Título: {titulo}
    Resumo: {resumo}
    """

    conteudo_reescrito = pedir_ia_groq(prompt_texto, temperatura=0.6)

    # Caixa de publicidade ÚNICA, no final, claramente identificada como anúncio.
    # Só aparece se você configurar um link de afiliado real na variável LINK_AFILIADO.
    caixa_publicidade = ""
    if LINK_AFILIADO:
        caixa_publicidade = f"""
        <div style="background-color: #fff8e1; border: 1px solid #f0d68a; border-radius: 10px; margin: 30px 0; padding: 20px; font-family: sans-serif;">
            <p style="font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 8px 0;">Publicidade</p>
            <p style="font-size: 15px; color: #333; margin: 0 0 12px 0;">Aproveite ofertas selecionadas enquanto navega pelo blog:</p>
            <a href="{LINK_AFILIADO}" target="_blank" rel="nofollow sponsored"
               style="background-color: #ff007f; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
               Ver ofertas
            </a>
        </div>
        """

    html_final = f"""{img1_html}
{conteudo_reescrito}
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
