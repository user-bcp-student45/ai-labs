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
