def reescrever_com_ia_anti_plagio(titulo, resumo, link_fonte, nome_fonte):
    # Geramos 4 imagens com seeds diferentes para não repetirem
    imgs = [f"https://picsum.photos/seed/{random.randint(1, 9999)}/800/400" for _ in range(4)]

    prompt_texto = f"""
    Você é um especialista em jornalismo digital e SEO.
    Escreva um artigo de notícia completo, descontraído e fluido em Português do Brasil com base nas informações fornecidas.

    REGRAS OBRIGATÓRIAS DE FORMATO (HTML PURO):
    1. Retorne APENAS HTML PURO. NUNCA use Markdown (sem **, sem #, sem listas soltas).
    2. TODOS os parágrafos sem exceção DEVEM estar envolvidos nas tags <p> e </p>.
    3. Crie 3 subtítulos usando a tag <h2>Subtítulo aqui</h2>.
    4. Crie 3 notas do autor usando a tag <p><em>(Nota do autor: ...)</em></p>.

    REGRAS PARA AS IMAGENS DO MEIO DO TEXTO:
    No meio do artigo (entre os parágrafos e subtítulos), você DEVE inserir as 3 tags de imagem abaixo exatamente como fornecidas:
    - [IMAGEM_2]
    - [IMAGEM_3]
    - [IMAGEM_4]

    REGRAS DOS LINKS DE AFILIADO (DILUÍDOS NO TEXTO):
    Não coloque os links no final! Insira-os naturalmente DENTRO das frases ao longo do texto:
    - ...para economizar no dia a dia, <a href="http://s.shopee.com.br/5VQHqQtgyf" target="_blank">confira esta seleção especial</a> de ofertas.
    - ...para ficar por dentro de tudo, <a href="http://cabinepopnews.blogspot.com" target="_blank">acesse mais notícias exclusivas</a> no blog.
    - ...se você busca soluções práticas, <a href="http://solucaodigitalshop.blogspot.com" target="_blank">veja as novidades aqui</a> na loja.
    - ...aproveite também para conferir e <a href="http://s.shopee.com.br/2qTBX58t8P" target="_blank">garantir descontos agora</a> nas promoções.

    Notícia Original ({nome_fonte}):
    Título: {titulo}
    Resumo: {resumo}
    """

    conteudo_reescrito = pedir_ia_groq(prompt_texto)

    # Solicita à IA um título para a matéria e textos alternativos/atributos SEO para as 4 imagens
    prompt_seo = f"""
    Com base no tema '{titulo}', gere os seguintes textos em Português do Brasil:
    1. Um título chamativo para a matéria (sem aspas).
    2. 4 textos alternativos curtos e focados em SEO para as imagens (1 para cada imagem).
    3. 4 textos de título (title) amigáveis para as imagens.

    Responda ESTRITAMENTE no seguinte formato JSON (sem blocos de código markdown):
    {{
      "titulo_post": "Título principal da matéria",
      "alts": ["alt imagem 1", "alt imagem 2", "alt imagem 3", "alt imagem 4"],
      "titles": ["title imagem 1", "title imagem 2", "title imagem 3", "title imagem 4"]
    }}
    """
    
    resposta_seo = pedir_ia_groq(prompt_seo)
    
    # Tratamento simples para extrair o JSON com segurança
    try:
        import json
        # Limpa possíveis formatações de markdown que a IA possa enviar
        json_limpo = resposta_seo.replace("```json", "").replace("```", "").strip()
        dados_seo = json.loads(json_limpo)
        novo_titulo = dados_seo.get("titulo_post", titulo)
        alts = dados_seo.get("alts", [titulo]*4)
        titles = dados_seo.get("titles", [titulo]*4)
    except Exception:
        # Backup caso ocorra erro no parse do JSON
        novo_titulo = pedir_ia_groq(f"Crie um título inédito para: '{titulo}'. Retorne só o texto.").replace('"', '').strip()
        alts = [f"Imagem sobre {novo_titulo}"] * 4
        titles = [f"Ilustração - {novo_titulo}"] * 4

    # Monta a estrutura HTML das 4 imagens com Alt e Title SEO
    img1_html = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{imgs[0]}" alt="{alts[0]}" title="{titles[0]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'
    img2_html = f'<div style="text-align: center; margin: 25px 0;"><img src="{imgs[1]}" alt="{alts[1]}" title="{titles[1]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'
    img3_html = f'<div style="text-align: center; margin: 25px 0;"><img src="{imgs[2]}" alt="{alts[2]}" title="{titles[2]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'
    img4_html = f'<div style="text-align: center; margin: 25px 0;"><img src="{imgs[3]}" alt="{alts[3]}" title="{titles[3]}" style="max-width:100%; height:auto; border-radius:8px;"/></div>'

    # Substitui os marcadores de imagem no corpo do texto pelas tags HTML das imagens
    conteudo_reescrito = conteudo_reescrito.replace("[IMAGEM_2]", img2_html)
    conteudo_reescrito = conteudo_reescrito.replace("[IMAGEM_3]", img3_html)
    conteudo_reescrito = conteudo_reescrito.replace("[IMAGEM_4]", img4_html)

    # Montagem do HTML completo com a 1ª imagem no topo
    html_final = f"""
    {img1_html}
    {conteudo_reescrito}
    <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
    <p style="font-size: 12px; color: gray; font-style: italic;">
        Fonte original: <a href="{link_fonte}" target="_blank" rel="noopener">{nome_fonte}</a>.
    </p>
    """

    return novo_titulo, html_final
