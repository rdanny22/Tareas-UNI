#!/usr/bin/env python3
"""Extrae el texto de un .docx a Markdown conservando la estructura.

Uso:
    python3 tools/extraer_docx.py documento.docx > salida.md

No requiere dependencias externas: lee el OOXML con la biblioteca estandar.
Conserva titulos y subtitulos como encabezados Markdown, las tablas como
tablas de tuberias y los parrafos de lista con guion.
"""
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

_RE_TITULO = re.compile(r"(?:heading|t[ií]tulo|titulo)\s*(\d)", re.IGNORECASE)
_RE_TITULO_NUM = re.compile(r"^[1-6]$")


def nivel_de_estilo(p):
    """Devuelve el nivel de encabezado (1-6) o 0 si es cuerpo de texto."""
    ppr = p.find(W + "pPr")
    if ppr is None:
        return 0
    ps = ppr.find(W + "pStyle")
    if ps is None:
        return 0
    estilo = (ps.get(W + "val") or "").strip()
    if estilo.lower() in ("title", "titulo", "título"):
        return 1
    m = _RE_TITULO.search(estilo)
    if m:
        return int(m.group(1))
    if _RE_TITULO_NUM.match(estilo):
        return int(estilo)
    return 0


def es_lista(p):
    ppr = p.find(W + "pPr")
    if ppr is None:
        return False
    return ppr.find(W + "numPr") is not None


def texto_de_parrafo(p):
    partes = []
    for nodo in p.iter():
        if nodo.tag == W + "t":
            partes.append(nodo.text or "")
        elif nodo.tag == W + "tab":
            partes.append("\t")
        elif nodo.tag == W + "br":
            partes.append("\n")
    return "".join(partes)


def fila_a_celdas(tr):
    celdas = []
    for tc in tr.findall(W + "tc"):
        trozos = [texto_de_parrafo(p) for p in tc.iter(W + "p")]
        celdas.append(" ".join(t.strip() for t in trozos if t.strip()))
    return celdas


def tabla_a_markdown(tbl):
    filas = [fila_a_celdas(tr) for tr in tbl.findall(W + "tr")]
    filas = [f for f in filas if any(c for c in f)]
    if not filas:
        return []
    ancho = max(len(f) for f in filas)
    filas = [f + [""] * (ancho - len(f)) for f in filas]
    salida = ["| " + " | ".join(filas[0]) + " |",
              "|" + "|".join(["---"] * ancho) + "|"]
    for f in filas[1:]:
        salida.append("| " + " | ".join(f) + " |")
    return salida


def procesar(elem, salida):
    for hijo in elem:
        if hijo.tag == W + "p":
            texto = texto_de_parrafo(hijo).strip()
            if not texto:
                continue
            nivel = nivel_de_estilo(hijo)
            if nivel:
                salida.append("#" * min(nivel, 6) + " " + texto)
            elif es_lista(hijo):
                salida.append("- " + texto)
            else:
                salida.append(texto)
        elif hijo.tag == W + "tbl":
            filas = tabla_a_markdown(hijo)
            if filas:
                salida.append("\n".join(filas))
        else:
            procesar(hijo, salida)


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python3 tools/extraer_docx.py documento.docx")
    ruta = sys.argv[1]
    with zipfile.ZipFile(ruta) as z:
        xml = z.read("word/document.xml")
    raiz = ET.fromstring(xml)
    cuerpo = raiz.find(W + "body")
    salida = []
    procesar(cuerpo, salida)
    texto = "\n\n".join(salida) + "\n"
    sys.stdout.write(texto)


if __name__ == "__main__":
    main()
