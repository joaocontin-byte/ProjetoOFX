import csv
from datetime import date
from io import BytesIO, StringIO
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from conexao import conectar
from ofx_service import ler_ofx, salvar_movimentacoes, sugerir_categoria_despesa

app = FastAPI(title="Projeto OFX API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Movimentacao(BaseModel):
    data: date
    valor: float
    descricao: str
    categoria: str


class Importacao(BaseModel):
    movimentacoes: list[Movimentacao]
    arquivo: str | None = None


@app.get("/api/health")
def health():
    try:
        banco = conectar()
        banco.close()
        return {"conectado": True}
    except Exception as erro:
        raise HTTPException(status_code=503, detail=f"Falha ao conectar ao banco: {erro}")


@app.post("/api/ofx/preview")
async def preview_ofx(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".ofx"):
        raise HTTPException(status_code=400, detail="Selecione um arquivo .ofx.")
    try:
        movimentos = ler_ofx(await file.read())
        entradas = sum((m["valor"] for m in movimentos if m["valor"] > 0), 0)
        saidas = sum((m["valor"] for m in movimentos if m["valor"] < 0), 0)
        categorias_sugeridas = list(dict.fromkeys(
            sugestao
            for movimento in movimentos if movimento["valor"] < 0
            if (sugestao := sugerir_categoria_despesa(movimento["descricao"]))
        ))

        return {
            "arquivo": file.filename,
            "quantidade": len(movimentos),
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas + saidas,
            "categorias_sugeridas": categorias_sugeridas,
            "movimentacoes": [
                {**m, "data": m["data"].isoformat(), "valor": float(m["valor"])}
                for m in movimentos
            ],
        }
    except Exception as erro:
        raise HTTPException(status_code=400, detail=f"Não foi possível ler o OFX: {erro}")


@app.post("/api/ofx/save")
def save_ofx(importacao: Importacao):
    try:
        salvar_movimentacoes([m.model_dump() for m in importacao.movimentacoes])
        return {"salvo": True, "quantidade": len(importacao.movimentacoes)}
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Falha ao salvar no banco: {erro}")


def _nome_arquivo(importacao, extensao):
    base = Path(importacao.arquivo or "movimentacoes").stem
    seguro = "".join(char for char in base if char.isascii() and (char.isalnum() or char in ("-", "_", " "))).strip()
    return f"{seguro or 'movimentacoes'}.{extensao}"


def _linhas_exportacao(movimentacoes):
    return [
        [m.data, m.descricao, m.categoria, "Entrada" if m.valor >= 0 else "Saída", m.valor]
        for m in movimentacoes
    ]


@app.post("/api/ofx/export/csv")
def export_csv(importacao: Importacao):
    conteudo = StringIO(newline="")
    escritor = csv.writer(conteudo, delimiter=";")
    escritor.writerow(["Data", "Descrição", "Categoria", "Tipo", "Valor (R$)"])
    for data, descricao, categoria, tipo, valor in _linhas_exportacao(importacao.movimentacoes):
        escritor.writerow([data.strftime("%d/%m/%Y"), descricao, categoria, tipo, f"{valor:.2f}".replace(".", ",")])
    return Response(
        content="\ufeff" + conteudo.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_nome_arquivo(importacao, "csv")}"'},
    )


@app.post("/api/ofx/export/pdf")
def export_pdf(importacao: Importacao):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from xml.sax.saxutils import escape

        buffer = BytesIO()
        workbook = SimpleDocTemplate(
            buffer, pagesize=landscape(A4),
            rightMargin=18 * mm, leftMargin=18 * mm,
            topMargin=17 * mm, bottomMargin=16 * mm,
            title="Relatório de movimentações",
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "OFXTitle", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=19, leading=23, textColor=colors.HexColor("#26372d"),
            alignment=0, spaceAfter=4,
        )
        sub_style = ParagraphStyle(
            "OFXSubtitle", parent=styles["Normal"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=colors.HexColor("#718078"),
        )
        cell_style = ParagraphStyle(
            "OFXCell", parent=styles["Normal"], fontName="Helvetica",
            fontSize=8, leading=10, textColor=colors.HexColor("#344139"),
        )
        header_style = ParagraphStyle(
            "OFXHeader", parent=cell_style, fontName="Helvetica-Bold",
            textColor=colors.white,
        )

        movements = importacao.movimentacoes
        entradas = sum(m.valor for m in movements if m.valor > 0)
        saidas = sum(m.valor for m in movements if m.valor < 0)

        def moeda(valor):
            return f"R$ {abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        story = [
            Paragraph("Relatório de movimentações", title_style),
            Paragraph(escape(importacao.arquivo or "Extrato OFX") + " - " + str(len(movements)) + " lançamentos", sub_style),
            Spacer(1, 8 * mm),
        ]
        summary = Table(
            [["ENTRADAS", "SAÍDAS", "SALDO DO ARQUIVO"],
             [moeda(entradas), moeda(saidas), moeda(entradas + saidas)]],
            colWidths=[82 * mm, 82 * mm, 82 * mm],
        )
        summary.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf5ef")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#63806c")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, 1), 12),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#26372d")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8faf8")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e9e3")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e9e3")),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.extend([summary, Spacer(1, 8 * mm)])

        table_data = [[
            Paragraph("DATA", header_style), Paragraph("DESCRIÇÃO", header_style),
            Paragraph("CATEGORIA", header_style), Paragraph("TIPO", header_style),
            Paragraph("VALOR", header_style),
        ]]
        for movement in movements:
            signed_value = moeda(movement.valor)
            if movement.valor < 0:
                signed_value = "- " + signed_value
            table_data.append([
                movement.data.strftime("%d/%m/%Y"),
                Paragraph(escape(movement.descricao), cell_style),
                Paragraph(escape(movement.categoria), cell_style),
                "Entrada" if movement.valor >= 0 else "Saída",
                signed_value,
            ])
        table = Table(table_data, colWidths=[27 * mm, 87 * mm, 68 * mm, 25 * mm, 39 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#347b5d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#344139")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9f7")]),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#347b5d")),
            ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor("#e7ece8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(table)

        def rodape(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#849087"))
            canvas.drawRightString(landscape(A4)[0] - 18 * mm, 8 * mm, f"Projeto OFX - Página {doc.page}")
            canvas.restoreState()

        workbook.build(story, onFirstPage=rodape, onLaterPages=rodape)
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{_nome_arquivo(importacao, "pdf")}"'},
        )
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Não foi possível gerar o PDF: {erro}")


@app.post("/api/ofx/export/excel")
def export_excel(importacao: Importacao):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Movimentações"
        sheet.append(["Data", "Descrição", "Categoria", "Tipo", "Valor (R$)"])
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="347B5D")
        for data, descricao, categoria, tipo, valor in _linhas_exportacao(importacao.movimentacoes):
            sheet.append([data, descricao, categoria, tipo, valor])
            sheet.cell(sheet.max_row, 1).number_format = "DD/MM/YYYY"
            sheet.cell(sheet.max_row, 5).number_format = '"R$" #,##0.00'
        sheet.column_dimensions["A"].width = 14
        sheet.column_dimensions["B"].width = 38
        sheet.column_dimensions["C"].width = 30
        sheet.column_dimensions["D"].width = 14
        sheet.column_dimensions["E"].width = 18
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

        arquivo = BytesIO()
        workbook.save(arquivo)
        return Response(
            content=arquivo.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{_nome_arquivo(importacao, "xlsx")}"'},
        )
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Não foi possível gerar o Excel: {erro}")












