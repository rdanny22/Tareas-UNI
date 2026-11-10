#!/usr/bin/env python3
"""Cuenta marcas de estilo generado en un texto y emite el inventario.

Uso:
    python3 tools/detectar_marcas.py texto.md

Lee el texto plano (Markdown o .txt) y agrupa las marcas por nivel:
lexico, sintactico, estructural, tipografico y de contenido. Para cada
categoria informa numero de ocurrencias y hasta tres ejemplos textuales
con su numero de linea.

Corresponde a la Fase 1 del prompt v3. No reescribe nada: solo diagnostica.
"""
import re
import sys
from collections import OrderedDict

# ---------------------------------------------------------------- utilidades


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def partir_oraciones(texto):
    """Divide en oraciones por . ! ? seguidos de espacio, sin cortar decimales."""
    plano = re.sub(r"\s+", " ", texto)
    crudas = re.split(r"(?<=[.!?])\s+(?=[«\"¿¡A-ZÁÉÍÓÚÑ])", plano)
    return [o.strip() for o in crudas if o.strip()]


def contar_palabras(texto):
    return len(re.findall(r"[\wáéíóúüñÁÉÍÓÚÜÑ]+", texto))


def numero_linea(texto, pos):
    return texto.count("\n", 0, pos) + 1


def contexto(texto, m, ancho=70):
    ini = max(0, m.start() - ancho // 2)
    fin = min(len(texto), m.end() + ancho // 2)
    frag = re.sub(r"\s+", " ", texto[ini:fin]).strip()
    return ("…" if ini > 0 else "") + frag + ("…" if fin < len(texto) else "")


def buscar_patron(texto, patron, flags=re.IGNORECASE):
    """Devuelve [(linea, ejemplo)] para un patron regex."""
    hits = []
    for m in re.finditer(patron, texto, flags):
        hits.append((numero_linea(texto, m.start()), contexto(texto, m)))
    return hits


# ---------------------------------------------------------------- marcas

LEXICO = OrderedDict([
    ("Muletillas de relleno", r"en el mundo actual|en la era digital|hoy en d[ií]a|"
                              r"en la actualidad|a lo largo de la historia|"
                              r"desde tiempos (remotos|inmemoriales)|"
                              r"es importante (destacar|recordar|mencionar|se[ñn]alar|notar)|"
                              r"cabe (resaltar|mencionar|destacar|se[ñn]alar|aclarar)|"
                              r"sin lugar a dudas|en definitiva|en resumen|"
                              r"para concluir|en este sentido|a continuaci[oó]n veremos|"
                              r"en este apartado|a continuaci[oó]n se (presenta|describe|aborda)|"
                              r"vale la pena (destacar|mencionar)|"
                              r"como (todos )?sabemos"),
    ("Intensificadores sin dato", r"\b(crucial(es)?|fundamental(es)?|clave|robusto|"
                                  r"robusta|vital(es)?|notablemente|significativamente|"
                                  r"de suma importancia|sumamente|indispensable|"
                                  r"extremadamente|altamente)\b"),
    ("Adjetivos valorativos", r"\b(innovador(a|es)?|poderoso|poderosa|revolucionari[oa]|"
                              r"esencial(es)?|vanguardista|integral(es)?|"
                              r"vers[aá]til(es)?|de clase mundial|puntero)\b"),
    ("Perífrasis que esconden el verbo", r"se (realiza|realiz[oó]|realizar|realizaron|"
                                         r"lleva a cabo|llev[oó] a cabo|llevar a cabo)|"
                                         r"llevar a cabo|hacer uso de|hace uso de|"
                                         r"se procede a|procede a (realizar|ejecutar)|"
                                         r"se efect[uú]a|efectuar una"),
    ("Anglicismos evitables", r"\b(framework|frameworks|insight|insights|leverage|"
                              r"seamless|key takeaways|best practices|approach|"
                              r"stakeholder|roadmap|mindset|data-driven|"
                              r"performance|features|deploy|deployment)\b"),
])

SINTACTICO = OrderedDict([
    ("Contraste vacío", r"no solo\b.{0,120}?\bsino tambi[eé]n|"
                        r"m[aá]s que \w+.{0,60}?es \w+|"
                        r"no se trata (solo )?de .{0,80}?, sino"),
    ("Arranque con gerundio", r"(?:^|[.!?]\s+|\n\s*\n\s*)[A-ZÁÉÍÓÚÑ]?\w*(?:ando|iendo)\s+\w"),
    ("Pasiva perifrástica", r"\b(fue|fueron|es|son|ha sido|han sido|"
                            r"puede ser|pueden ser)\s+\w+(?:ado|ada|ados|adas|ido|ida|idos|idas)\s+por\b"),
])

CONECTORES_INICIALES = (r"Adem[aá]s|Asimismo|Por otro lado|En este sentido|"
                        r"Sin embargo|No obstante|Por consiguiente|En consecuencia|"
                        r"De igual manera|Igualmente|Por su parte|En primer lugar|"
                        r"En segundo lugar|Finalmente|Por [uú]ltimo")

ESTRUCTURAL = OrderedDict([
    ("Cierre de sección o moraleja", r"en (conclusi[oó]n|s[íi]ntesis|suma)|"
                                     r"para (finalizar|terminar|concluir)|"
                                     r"en [uú]ltima instancia|el futuro de \w+ "
                                     r"(es|ser[aá])|el potencial de"),
    ("Anuncio de lo que viene", r"a continuaci[oó]n|en la siguiente secci[oó]n|"
                                 r"el presente (documento|informe|trabajo) "
                                 r"(tiene como|busca|pretende)|"
                                 r"se (presentar[aá]|describir[aá]|abordar[aá])"),
])

TIPOGRAFICO = OrderedDict([
    ("Raya como conector", r"—"),
    ("Negritas de énfasis", r"\*\*[^*\n]{1,60}\*\*"),
    ("Comillas mezcladas", r"[«»„“”\"]"),
])

# ---------------------------------------------------------------- analisis


def analizar(ruta):
    texto = leer(ruta)
    palabras = contar_palabras(texto)
    oraciones = partir_oraciones(texto)
    lineas = texto.splitlines()

    reporte = []
    total_lexico = total_sint = total_est = total_tip = 0

    for nombre, patron in LEXICO.items():
        hits = buscar_patron(texto, patron)
        total_lexico += len(hits)
        reporte.append(("lexico", nombre, hits))

    for nombre, patron in SINTACTICO.items():
        hits = buscar_patron(texto, patron)
        total_sint += len(hits)
        reporte.append(("sintactico", nombre, hits))

    # Oraciones largas con subordinacion encadenada
    largas = []
    for o in oraciones:
        n = contar_palabras(o)
        if n > 40 and len(re.findall(r"\bque\b|\bque\b|\bcuando\b|\bmientras\b", o)) >= 3:
            idx = texto.find(o[:40])
            largas.append((numero_linea(texto, idx) if idx >= 0 else 0, o[:120] + "…"))
    total_sint += len(largas)
    reporte.append(("sintactico", "Oración >40 palabras con 3+ subordinadas", largas))

    # Conectores al inicio de parrafo
    conect = []
    for i, linea in enumerate(lineas, 1):
        if re.match(r"^\s*(?:" + CONECTORES_INICIALES + r")\b", linea):
            conect.append((i, re.sub(r"\s+", " ", linea)[:100] + "…"))
    total_sint += len(conect)
    reporte.append(("sintactico", "Párrafo que abre con conector", conect))

    # Triadas: tres elementos en serie (heuristico, revisar a mano)
    triadas = buscar_patron(texto, r"\b\w+,\s+\w+\s+y\s+\w+\.")
    total_sint += len(triadas)
    reporte.append(("sintactico", "Serie de tres elementos (heurístico)", triadas))

    for nombre, patron in ESTRUCTURAL.items():
        hits = buscar_patron(texto, patron)
        total_est += len(hits)
        reporte.append(("estructural", nombre, hits))

    # Simetria de apartados: longitud de cada seccion
    secciones, actual, buffer_len = [], None, 0
    for linea in lineas:
        if linea.startswith("#"):
            if actual is not None:
                secciones.append((actual, buffer_len))
            actual, buffer_len = linea.strip("# ").strip(), 0
        else:
            buffer_len += contar_palabras(linea)
    if actual is not None:
        secciones.append((actual, buffer_len))
    simetria = []
    if len(secciones) >= 3:
        largos = [n for _, n in secciones if n > 0]
        if largos:
            media = sum(largos) / len(largos)
            desvio = (sum((n - media) ** 2 for n in largos) / len(largos)) ** 0.5
            if media and desvio / media < 0.25:
                simetria.append((0, f"Secciones de extensión casi idéntica "
                                    f"(media {media:.0f} palabras, CV {desvio/media:.2f})"))
    total_est += len(simetria)
    reporte.append(("estructural", "Simetría forzada entre apartados", simetria))

    rayas = buscar_patron(texto, r"—")
    negritas = buscar_patron(texto, r"\*\*[^*\n]{1,60}\*\*")
    total_tip = len(rayas) + len(negritas)
    reporte.append(("tipografico", "Rayas (máx. 1 por 1000 palabras)", rayas))
    reporte.append(("tipografico", "Negritas de énfasis", negritas))
    densidad = f"{len(rayas) / palabras * 1000:.2f}" if palabras else "0"

    # Cifras sin cita
    sin_fuente = []
    for m in re.finditer(r"[^.]*\d+(?:[.,]\d+)?\s?%[^.]*\.", texto):
        frag = m.group(0)
        if not re.search(r"\(\s*[A-ZÁÉÍÓÚÑ][^)]{0,40},?\s*\d{4}\s*\)|\[\d+\]", frag):
            limpio = re.sub(r"\s+", " ", frag).strip()
            desplazamiento = m.start() + len(frag) - len(frag.lstrip())
            sin_fuente.append((numero_linea(texto, desplazamiento), limpio[:110]))
    reporte.append(("contenido", "Cifra porcentual sin cita", sin_fuente))

    # ------------------------------------------------------------- salida
    print("=" * 72)
    print(f"INVENTARIO DE MARCAS — {ruta}")
    print("=" * 72)
    print(f"Palabras: {palabras}   Oraciones: {len(oraciones)}   "
          f"Media de palabras por oración: "
          f"{palabras / len(oraciones):.1f}" if oraciones else "")
    print()

    nivel_actual = None
    for nivel, nombre, hits in reporte:
        if nivel != nivel_actual:
            print(f"\n--- NIVEL {nivel.upper()} " + "-" * (50 - len(nivel)))
            nivel_actual = nivel
        marca = "[X]" if hits else "[ ]"
        print(f"{marca} {nombre}: {len(hits)}")
        if nombre.startswith("Rayas"):
            print(f"    Densidad: {densidad} por 1000 palabras (límite: 1)")
        for linea, ejemplo in hits[:3]:
            etiqueta = f"    L{linea}: " if linea else "    "
            print(f"{etiqueta}{ejemplo}")

    print("\n" + "=" * 72)
    print("RESUMEN")
    print(f"  Léxico:        {total_lexico}")
    print(f"  Sintáctico:    {total_sint}")
    print(f"  Estructural:   {total_est}")
    print(f"  Tipográfico:   {total_tip}")
    print("=" * 72)
    print("Nota: las series de tres elementos y la simetría entre apartados son")
    print("heurísticas. Confírmalas a mano antes de reescribir.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python3 tools/detectar_marcas.py texto.md")
    analizar(sys.argv[1])
