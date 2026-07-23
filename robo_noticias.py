def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    # --- 1. Extrai uma palavra-chave para as imagens ---
    prompt_keyword = (
        f"Com base no título '{titulo}', dê apenas uma palavra em inglês (singula, sem espaços) "
        "que represente o assunto principal. Exemplo: 'f1', 'football', 'technology', 'politics'. "
        "Responda APENAS com a palavra."
    )
    keyword = pedir_ia_groq(prompt_keyword).strip().lower()
    if not keyword:
        keyword = "news"

    # --- 2. Gera de 4 a 6 URLs de imagens do Unsplash com seeds diferentes ---
    num_imagens = 5  # pode ajustar
    imagens = []
    for i in range(num_imagens):
        # Usa seed aleatório para variar, mas mantém a keyword
        seed = random.randint(1, 9999)
        url = f"https://source.unsplash.com/seed/{seed}/800x400/?{keyword}"
        alt_text = f"Imagem ilustrativa sobre {keyword} – parte {i+1}"
        title_text = f"{keyword.capitalize()} – ilustração {i+1}"
        imagens.append({"url": url, "alt": alt_text, "title": title_text})

    # --- 3. Gera o corpo do artigo com um prompt ultra-detalhado ---
    prompt_texto = f"""
    Você é um jornalista experiente e redator de um blog de notícias popular no Brasil.
    Escreva um artigo extenso, aprofundado e muito bem estruturado em Português do Brasil.

    **REGRAS OBRIGATÓRIAS:**

    1. **Tamanho:** O artigo deve ter, no mínimo, 1500 palavras (conteúdo rico e detalhado).
    2. **Títulos e subtítulos:** Use pelo menos 5 subtítulos com a tag <h2> (ex: <h2>Subtítulo impactante</h2>).
    3. **Parágrafos:** Todos os parágrafos devem estar envolvidos em <p> e </p>.
    4. **Notas do autor:** Insira 3 ou mais blocos de notas com tom irônico, engraçado ou reflexivo, usando <blockquote> ou <div style="...">. Cada nota deve ter um conteúdo único.
    5. **Tabela:** Crie pelo menos uma tabela HTML (<table>) com dados relevantes (comparativos, cronologia, etc.) e estilize com bordas simples.
    6. **Lista:** Inclua uma lista (<ul> com <li>) com dicas, recomendações ou itens importantes.
    7. **Imagens:** Distribua as imagens ao longo do texto (não só no início). Posicione cada imagem em um local adequado, usando a seguinte tag HTML para cada uma:
       <div style="text-align: center; margin: 25px 0;">
           <img src="URL_DA_IMAGEM" alt="DESCRIÇÃO" title="TÍTULO" style="max-width:100%; height:auto; border-radius:8px;"/>
       </div>
       **IMPORTANTE:** Use as 5 imagens fornecidas abaixo, inserindo cada uma em momentos diferentes do texto. Não use outras imagens.

       Lista de imagens (use todas):
       1) URL: {imagens[0]['url']}  |  alt: "{imagens[0]['alt']}"  |  title: "{imagens[0]['title']}"
       2) URL: {imagens[1]['url']}  |  alt: "{imagens[1]['alt']}"  |  title: "{imagens[1]['title']}"
       3) URL: {imagens[2]['url']}  |  alt: "{imagens[2]['alt']}"  |  title: "{imagens[2]['title']}"
       4) URL: {imagens[3]['url']}  |  alt: "{imagens[3]['alt']}"  |  title: "{imagens[3]['title']}"
       5) URL: {imagens[4]['url']}  |  alt: "{imagens[4]['alt']}"  |  title: "{imagens[4]['title']}"

    8. **Links de afiliado:** Dilua os seguintes links NATURALMENTE dentro de frases (não apenas no final), por exemplo: "para economizar no dia a dia, <a href='http://s.shopee.com.br/5VQHqQtgyf' target='_blank'>confira esta seleção</a>".
       Links disponíveis:
       - http://www.effectivecpmnetwork.com/b305upis?key=2a12ca9ddb56a3b0e36ad136d078d1d6
       - http://www.effectivecpmnetwork.com/vvzf3t934c?key=759e7575ec4be9a13b09fc83d86bdcb1
       - http://s.shopee.com.br/5VQHqQtgyf
       - http://www.instagram.com/auracristalencantos
       - http://solucaodigitalshop.blogspot.com
       - http://cabinepopnews.blogspot.com
       - http://s.shopee.com.br/2qTBX58t8P
       - http://s.shopee.com.br/9zwM4HodQI

    9. **Formato de saída:** Retorne APENAS o conteúdo HTML puro (sem ```html, sem cabeçalho, sem explicações). Comece diretamente com o primeiro <h2> ou <p>.

    10. **Citação da fonte:** Ao final, faça uma referência clara à fonte original, conforme o modelo:
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="font-size: 13px; color: #555; font-style: italic; margin-top: 15px;">
            📌 <strong>Fonte da notícia original:</strong> <a href="{link_fonte}" target="_blank" rel="noopener noreferrer">{nome_fonte}</a>
        </p>

    **Conteúdo original (base para o artigo):**
    Título: {titulo}
    Resumo: {resumo}
    """

    # --- 4. Chama a IA para gerar o artigo ---
    conteudo_reescrito = pedir_ia_groq(prompt_texto)

    # --- 5. Gera o título inédito (separadamente) ---
    prompt_titulo = (
        f"Crie um título inédito, chamativo e em português do Brasil para esta notícia: '{titulo}'. "
        f"Responda APENAS com o título em texto puro, sem aspas, sem tags HTML."
    )
    novo_titulo = pedir_ia_groq(prompt_titulo).replace('"', '').replace('\n', ' ').strip()

    # --- 6. Monta o HTML final, já com as imagens inseridas pela IA ---
    # A IA já deve ter colocado as imagens no corpo, então só adicionamos a referência final.
    # Mas vamos garantir que a fonte seja incluída (a IA já tem a instrução).
    # Se por acaso a IA não colocou, adicionamos no final.

    # Verifica se o rodapé da fonte já está presente; se não, adiciona.
    if 'Fonte da notícia original' not in conteudo_reescrito:
        rodape = f"""
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="font-size: 13px; color: #555; font-style: italic; margin-top: 15px;">
            📌 <strong>Fonte da notícia original:</strong> <a href="{link_fonte}" target="_blank" rel="noopener noreferrer">{nome_fonte}</a>
        </p>
        """
        conteudo_reescrito += rodape

    return novo_titulo, conteudo_reescrito
