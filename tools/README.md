# Herramientas de diagnóstico

Utilidades para ejecutar la Fase 1 del prompt `prompts/prompt-redaccion-academica.md` sobre documentos reales. Solo biblioteca estándar de Python 3, sin dependencias.

## 1. Extraer el texto de un .docx

```bash
python3 tools/extraer_docx.py documento.docx > documento.md
```

Conserva la jerarquía de apartados como encabezados Markdown, las tablas como tablas de tuberías y los párrafos de lista con guion. Sirve como texto de trabajo para el diagnóstico y para revisar la estructura sin abrir Word.

## 2. Contar marcas de estilo generado

```bash
python3 tools/detectar_marcas.py documento.md
```

Emite el inventario de la Fase 1 agrupado por nivel (léxico, sintáctico, estructural, tipográfico y de contenido), con el número de ocurrencias, la línea y un ejemplo textual de cada tipo. Marca con `[ ]` las categorías sin hallazgos, para dejar constancia de que se revisaron.

Además calcula tres métricas que ninguna revisión a ojo da de forma fiable:

- media de palabras por oración y recuento de oraciones de más de 40 palabras con subordinación encadenada;
- densidad de rayas por cada mil palabras (el prompt fija el límite en una);
- coeficiente de variación de la extensión de los apartados, que detecta la simetría forzada típica de plantilla.

## Limitaciones

La detección de series de tres elementos y la de simetría entre apartados son heurísticas: confírmalas a mano antes de reescribir. El recuento tampoco distingue una muletilla legítima de una de relleno, porque eso depende del contexto. El inventario orienta la revisión; no la sustituye.
