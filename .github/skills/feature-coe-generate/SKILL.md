---
name: feature-coe-generate
description: Generar formato COE con la información relacionada al requerimiento HU-01.
---

# Skill: Feature Generate -> Spec Checklist

## 1) Metadata
- **Skill ID:** feature-coe-generate
- **Version:** 0.1.0
- **Purpose:** generar coe de la HU.
- **Audience (roles):** DEV, QA, Tech Lead
- **When to use:** Antes del congelamiento debe crearse correctamente el COE.
- **When NOT to use:** Cambios triviales como typos o tareas sin impacto funcional.
- **Sensitive inputs:** No incluyas datos reales de clientes, credenciales, secretos, tokens ni URLs internas no autorizadas.
- **Expected output:** Markdown estructurado mediante la sección Output a continuación.

## 2) Inputs
Proporciona la información en este formato:

- **Nombre Requerimiento:**
- **Responsable:**
- **Aplicativo:**
- **Nombre QA:**
- **Detalle Funcional:** 
- **Detalle Tecnico:** 

## 3) Output
Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Resumen de Cambio**
2. **Detalle Solución**
    - Dentro del alcance
    - Fuera del alcance
3. **Componentes Impactados**
4. **Pruebas Sugeridas**

## 4) Constraints
- No inventes requisitos: si falta información, inclúyela bajo **Preguntas abiertas**.
- No propongas secciones fuera de lo solicitado para la creación del COE.
- No incluyas datos sensibles ni secretos.
- El plan de validación debe incluir al menos un elemento de evidencia concreto, como salida de pruebas, un checklist o un archivo actualizado.
- Mantén la salida en un máximo de 1-2 páginas para que siga siendo usable.

## 5) Validation Rules
La salida es válida si:
- Incluye todas las secciones definidas en Output.
- Tiene al menos 3 tareas para cada rol central: Tech Lead, Backend y QA, o explica por qué un rol no aplica.
- Incluye al menos 2 riesgos con mitigaciones.
- No contiene datos sensibles ni secretos.
- No contiene supuestos no declarados.

## 6) Evidence
Adjunta o referencia estos elementos en el PR o entrega:
- `SKILL.md` versionado.
- `examples/input.sample.md`.
- `examples/output.sample.md`.
- Tag de versión para el Skill, como `skill-feature-coe-generate-v0.1.0`.