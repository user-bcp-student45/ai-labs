# Parametrizar filtros e inserciones SQL en la API

## Fuente
Hallazgo aprobado **H-API-03 — Filtros e inserts SQL concatenados**, en [HALLAZGOS.md](./HALLAZGOS.md).

- **Evidencia:** `api/app/main.py:70,84,93`. Los valores de query y del cuerpo se incorporan directamente a sentencias SQL.
- **Impacto:** comillas o expresiones inesperadas pueden alterar las consultas, provocar errores o afectar datos.

## Contexto actual
Las rutas de la API construyen filtros e inserciones SQL incorporando valores de entrada en las sentencias. Esto afecta las operaciones de tareas y resumen que consultan o modifican datos.

## Problema confirmado
Los valores recibidos de los clientes pueden modificar la estructura o el significado de consultas SQL en lugar de tratarse únicamente como datos. Esto puede causar resultados no previstos, errores o cambios no deseados en la persistencia.

## Comportamiento a preservar
- Se conservan los endpoints, métodos HTTP y formatos de solicitud y respuesta actualmente usados por el frontend.
- `GET /api/tasks` continúa devolviendo la lista de tareas con sus campos actuales; cuando corresponda, el filtro de propietario mantiene el comportamiento autorizado vigente.
- `POST /api/tasks` continúa creando una tarea y devolviendo la tarea creada con HTTP 201.
- `GET /api/summary` conserva el formato de su respuesta y el cálculo de sus métricas.
- La autorización de acceso a los datos sigue ligada a la identidad verificada; los valores de entrada no deben conceder acceso a datos de otra identidad.

## Alcance
- Tratar los valores externos usados en filtros e inserciones SQL como datos, sin que alteren la estructura o semántica prevista de las consultas.
- Mantener los resultados esperados para entradas válidas, incluidos valores que contengan caracteres especiales legítimos.
- Verificar el comportamiento de las operaciones afectadas ante entradas que intenten alterar la consulta.

## Fuera de alcance
- Cambiar los endpoints, formatos de solicitud o respuesta, o reglas funcionales de tareas y resumen.
- Cambiar el mecanismo de autenticación o autorización.
- Modificar hallazgos distintos de H-API-03.

## Criterios de aceptación
1. Los valores recibidos para filtros e inserciones se procesan como datos y no pueden cambiar la estructura ni la intención de las consultas SQL.
2. Entradas con caracteres especiales legítimos se procesan conforme a su valor, sin errores atribuibles a la composición de SQL.
3. Las entradas diseñadas para alterar una consulta no permiten leer, crear o modificar datos fuera de la operación autorizada.
4. Las operaciones afectadas conservan los endpoints, códigos de estado y formatos de respuesta existentes.
5. El acceso a los datos continúa limitado por la identidad verificada, sin otorgar autoridad adicional a valores enviados por el cliente.

## Contratos afectados/protegidos
- **API protegida:** conservar los endpoints y formatos utilizados por el frontend.
- **Seguridad de datos protegida:** mantener consultas parametrizadas y autorización ligada a la identidad.
- **Operaciones relacionadas:** `GET /api/tasks`, `POST /api/tasks` y `GET /api/summary`, conservando sus contratos observados.

## Riesgos, supuestos y preguntas abiertas
- **Riesgo:** cambios en el tratamiento de valores pueden alterar resultados si se dependía accidentalmente de la interpretación del SQL concatenado.
- **Supuesto:** los valores que contengan caracteres especiales legítimos deben seguir siendo admisibles como datos; el hallazgo no define restricciones adicionales de validación.
- **Preguntas abiertas:** ninguna para definir el comportamiento funcional de esta especificación.
