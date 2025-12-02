from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    """
    Função Genérica: Recebe um HTML e devolve um arquivo PDF em memória (bytes).
    """
    template = get_template(template_src)
    html  = template.render(context_dict)
    
    # Cria um buffer na memória (como se fosse um arquivo temporário)
    result = BytesIO()
    
    # A mágica da conversão
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue() # Retorna os dados binários do PDF
    return None