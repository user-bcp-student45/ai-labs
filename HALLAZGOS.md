# Hallazgos — Discovery

## API

### Contrato observado (no acordado)

`docs/ENDPOINTS.md` no existe; lo siguiente se deriva de `api/app/main.py` y no representa una decision de cambio.

- Todas las rutas dependen de `legacy_identity`, que espera el header `Authorization` con esquema Bearer, seguido de Base64 decodificado a `username|role|expiry|secret`. Se compara el secreto fijo y se comprueba la expiracion; no se verifica una firma criptografica, emisor ni audiencia. Los errores de validacion responden HTTP 401.
- `GET /api/tasks?owner=...` devuelve una lista de tareas con `id`, `title`, `description`, `status`, `owner`, `priority` y `createdAt`. Si se omite `owner`, usa el usuario del token.
- `POST /api/tasks` recibe un objeto JSON; devuelve una tarea con esos mismos campos y HTTP 201. Si no se incluye `owner`, usa el usuario del token.
- `GET /api/summary?owner=...` devuelve `owner`, `total`, `byStatus` y `highPriorityOpen`; si se omite `owner`, usa el usuario del token.
- `POST /api/requirements` recibe un archivo multipart `file`, guarda su contenido bajo el directorio de uploads y devuelve `owner`, `fileName`, `storedAt` y `size`, con HTTP 201.
- `GET /api/backend-health` consulta la URL configurada en `AUTH_HEALTH_URL` (o `http://localhost:8080/q/health`) y devuelve `requestedBy`, `status` y `body`.
- La aplicacion inicializa/consulta SQLite en `create_app`; las rutas de tareas consultan o insertan en la tabla `tasks`. El CORS observado permite cualquier origen, metodo y header, junto con credenciales.

### Matriz de seguimiento

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Token Base64 con secreto embebido | Vulnerabilidad | El contenido solo se decodifica y compara contra un secreto estatico; no hay firma criptografica ni validacion de emisor/audiencia. Si el secreto se conoce o se filtra, la identidad del token puede falsificarse; ademas, el detalle de excepcion se agrega al error 401. | api/app/security.py:29-62 | alta | Resuelto |
| H-API-02 | api | Acceso a tareas por `owner` controlado por cliente | Vulnerabilidad | `owner` de la query reemplaza la identidad del token y el `owner` del cuerpo se acepta al crear. Un usuario puede consultar el conjunto de otro propietario y asignar tareas a otro owner, sin comprobar rol. | api/app/routes.py:27-54, api/app/services.py:17-50 | alta | Resuelto |
| H-API-03 | api | Filtros e inserts SQL concatenados | Vulnerabilidad | Valores de query y del cuerpo se incorporan directamente a sentencias SQL; comillas o expresiones inesperadas pueden alterar la consulta, provocar errores o afectar datos. | api/app/main.py:70,84,93 | alta | Aprobado |
| H-API-04 | api | Nombre de archivo subido se usa directamente | Vulnerabilidad | El nombre proporcionado por el cliente se concatena al directorio y se escribe sin normalizacion, limite de tamano ni lista de extensiones. Puede permitir escritura fuera del destino previsto o consumo excesivo de almacenamiento. | api/app/main.py:107-111 | alta | Aprobado |
| H-API-05 | api | Dependencias SCA fijadas en versiones candidatas del reto | Vulnerabilidad | `urllib3` y `python-multipart` estan fijadas a las versiones indicadas por el reto. El pin confirma las versiones instaladas declaradas, pero no confirma por si solo un CVE aplicable; falta verificar advisories y alcance. | api/requirements.txt:4-5 | media | Aprobado |
| H-API-06 | api | Rutas, persistencia, reglas y serializacion concentradas en un modulo | Refactor | `create_app` inicializa SQLite y declara rutas que ejecutan SQL, calculan el resumen, gestionan archivos y serializan tareas. Este acoplamiento dificulta probar y cambiar responsabilidades de forma aislada. | api/app/main.py:29-59,67-124 | media | Aprobado |
| H-API-07 | api | Tipado crudo, excepciones amplias y condicionales anidados | Refactor | Las rutas y respuestas usan `dict[str, Any]`, hay capturas de `Exception` y el resumen anida condicionales; esto reduce validacion de entradas y claridad de errores/reglas. La duplicacion mencionada en RETO.md no se confirma como hallazgo independiente con la evidencia revisada. | api/app/main.py:17-25,56,68,78,91-105,115-121 | baja | Aprobado |

### Resolucion — alcance H-API-01 y H-API-02

- **H-API-01:** la API verifica tokens JWT con firma, algoritmo permitido, emisor, audiencia y claims obligatorios; los errores de token se devuelven con un mensaje generico. La coordinacion con el emisor externo y la configuracion previa al despliegue siguen pendientes.
- **H-API-02:** las lecturas y creaciones derivan el owner de la identidad verificada; los valores `owner` enviados por query o cuerpo no otorgan acceso ni asignan propiedad.

### Candidatos para revision humana

#### H-API-08 — CORS permite origenes arbitrarios con credenciales
- Estado: CANDIDATO
- Evidencia: `api/app/main.py:57-62` configura `allow_origins=["*"]`, `allow_credentials=True` y permite cualquier metodo y header.
- Impacto: cualquier origen web puede iniciar solicitudes cross-origin y, cuando presenta un token de acceso valido, leer respuestas de la API. Esto no elimina el requisito de autenticacion, pero deja sin restriccion de origen el acceso desde navegadores.
- Prioridad propuesta: Baja; confirmar primero cuales son los origenes de frontend autorizados y el modelo de credenciales esperado.
- Contrato potencialmente afectado: acceso desde navegador a `/api/tasks`, `/api/summary`, `/api/requirements` y `/api/backend-health`.
- Como validarlo: enviar una solicitud preflight `OPTIONS` con un `Origin` no autorizado y verificar si la respuesta refleja ese origen y `Access-Control-Allow-Credentials: true`; repetir con el origen real del frontend y comparar el comportamiento esperado.

#### H-API-09 — Subidas con el mismo nombre reemplazan el archivo anterior
- Estado: CANDIDATO
- Evidencia: `api/app/upload_service.py:35-39` construye la ruta de destino solo con el nombre normalizado y escribe con `Path.write_bytes`, que reemplaza el contenido existente.
- Impacto: dos usuarios autenticados que suban un requisito con el mismo nombre comparten destino; la segunda subida puede sobrescribir el contenido de la primera, aunque la respuesta identifique un propietario distinto.
- Prioridad propuesta: Media; depende de si los archivos deben conservarse por usuario o por carga.
- Contrato potencialmente afectado: `POST /api/requirements`, en particular la correspondencia entre `owner`, `fileName`, `storedAt` y el contenido persistido.
- Como validarlo: con un directorio temporal, subir secuencialmente el mismo nombre desde dos identidades con contenidos diferentes y comprobar si la primera carga sigue intacta; definir el comportamiento esperado (aislar, versionar o rechazar colisiones).

#### H-API-10 — El API acepta estados y prioridades no definidos por las reglas del resumen
- Estado: CANDIDATO
- Evidencia: `api/app/models.py:6-11` declara `status` y `priority` como `str` sin restricciones; `api/app/services.py:8-9,58-62` solo identifica `HIGH` y estados cerrados `DONE`/`ARCHIVED`.
- Impacto: `POST /api/tasks` puede persistir valores no reconocidos. Luego, `GET /api/summary` los cuenta como estados literales en `byStatus` y trata cualquier estado no cerrado como abierto, lo que puede producir métricas inconsistentes.
- Prioridad propuesta: Media; confirmar el vocabulario de estados y prioridades requerido por el producto antes de restringir entradas.
- Contrato potencialmente afectado: los valores aceptados por `POST /api/tasks` y la semantica de `byStatus` y `highPriorityOpen` en `GET /api/summary`.
- Como validarlo: probar la creacion con estados y prioridades fuera de los valores usados por los datos iniciales y las reglas de resumen; observar respuesta y agregados, y acordar previamente si deben rechazarse o admitirse como valores extensibles.
