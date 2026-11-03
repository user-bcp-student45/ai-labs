# Decisión de arquitectura — H-API-03

## Impacto
El hallazgo afecta el límite entre las rutas de tareas/resumen y la persistencia SQLite. Una composición insegura de SQL podría cambiar el significado de consultas o inserciones. La evidencia original cita `api/app/main.py`, pero el código actual concentra esas operaciones en `api/app/repository.py`; `api/app/main.py` configura la conexión e instancia el repositorio.

La inspección de las operaciones SQL actuales de `TaskRepository` muestra consultas parametrizadas para los valores externos de lectura e inserción. Por tanto, el defecto descrito no se observa en esas operaciones en el estado actual; la evidencia original corresponde a una versión anterior o a código que ya fue corregido.

## Componentes afectados
- `api/app/repository.py`: consultas y escritura SQLite de tareas; límite principal donde se deben enlazar como parámetros los valores externos.
- `api/app/services.py`: delega las lecturas y creación al repositorio; no requiere cambios de arquitectura para esta spec.
- `api/app/routes.py`: expone las operaciones `/api/tasks` y `/api/summary`; debe conservar sus contratos, sin incorporar SQL.
- `api/app/main.py`: composición de la conexión, repositorio, servicio y rutas; no debe volver a concentrar consultas.
- `api/tests/test_api.py`: pruebas de contrato y de manejo de valores con caracteres especiales.

## Contratos protegidos
- Mantener `GET /api/tasks`, `POST /api/tasks` y `GET /api/summary`, sus códigos de estado y formatos usados por el frontend.
- Mantener la propiedad y el acceso a tareas ligados a la identidad verificada.
- Tratar entradas externas como valores de datos y no como parte de la estructura SQL.
- No modificar contratos de autenticación ni ampliar el alcance a otros hallazgos.

## Estrategia incremental
1. Confirmar que la evidencia histórica de H-API-03 corresponde a una versión anterior y registrar el estado actual como referencia; no revertir la separación existente entre rutas, servicio y repositorio.
2. Añadir o completar pruebas de caracterización en `api/tests/test_api.py` para valores legítimos con comillas/caracteres especiales en campos de tarea y para consultas/resúmenes, verificando persistencia, aislamiento de propietario y formas de respuesta.
3. Revisar todas las operaciones SQL del repositorio alcanzadas por la spec. Si alguna interpolara datos externos, parametrizar únicamente esa operación y añadir una prueba focalizada; conservar la estructura de capas actual.
4. Ejecutar las pruebas del componente API y revisar el diff para confirmar que no cambian endpoints, serialización ni reglas ajenas al hallazgo.

**Decisión:** conservar el repositorio actual como único punto de acceso SQL de tareas y usar parámetros de SQLite para todo valor externo. No crear capas o abstracciones nuevas mientras el repositorio siga siendo pequeño y las operaciones permanezcan localizadas. Como el patrón ya está aplicado, el cambio mínimo es añadir una prueba de regresión; no se modifica código de producción.

## Pruebas necesarias
- Caracterizar respuesta, status code y campos de `GET /api/tasks`, `POST /api/tasks` y `GET /api/summary` para entradas ordinarias.
- **Pasó:** prueba focalizada de `test_sql_special_characters_are_treated_as_data` (1 passed). Comprueba que un identificador autenticado con texto SQL se trate como literal en listados y resúmenes; además, inserta y recupera texto con comillas sin alterar las tareas de otro propietario.
- **Pasó:** `python tools/lab.py test api` (14 passed; cobertura total 95.52%, umbral requerido 85%).
- **Pasó:** `git diff --check`.
- **Aviso no bloqueante:** pytest reportó una advertencia deprecada de Starlette sobre `httpx` y `httpx2`.

## Riesgos / trade-offs
- **Evidencia desactualizada:** la ubicación original en `api/app/main.py` no coincide con la estructura y las consultas actuales; implementar basándose solo en esas líneas podría duplicar trabajo o tocar el componente equivocado.
- **Compatibilidad:** interpretar caracteres especiales literalmente puede diferir de resultados accidentales producidos por SQL concatenado; prevalece el contrato y el tratamiento de entradas como datos.
- **Cobertura:** la nueva regresión cubre los patrones de caracteres especiales en los endpoints de lectura, resumen e inserción observados; si se incorporan nuevas consultas SQL con valores externos, deberán añadirse pruebas equivalentes.
- **Trade-off:** mantener SQL explícito en el repositorio evita abstracciones innecesarias; el costo es que cada nueva consulta debe seguir el mismo estándar de parametrización y quedar cubierta por pruebas.

## Decisiones abiertas
- Ninguna para el alcance implementado. La revisión humana del cambio sigue pendiente antes de cualquier integración.

## Resultado de implementación
- Cambio realizado: se añadió una prueba de regresión; no hubo modificaciones de producción porque las operaciones actuales ya parametrizan los valores.
- Riesgo residual: la evidencia del hallazgo apunta a una ruta histórica que ya no contiene dichas consultas; conservar la referencia histórica del hallazgo permite rastrear el origen.
- Preparación de PR: no se creó un PR ni se hizo push, conforme a la restricción local del Día 1.
