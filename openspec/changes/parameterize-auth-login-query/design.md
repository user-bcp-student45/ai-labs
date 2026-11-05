# Design

## Context

Motivación y alcance: ver [proposal.md](proposal.md) y [specs/auth-login/spec.md](specs/auth-login/spec.md). Issue de referencia: `user-bcp-student45/ai-labs#23` (H-AUTH-01). Componente: `auth/` (Quarkus 3.27, Java 21, SQLite vía JDBC).

Estado actual observado (solo lectura):

- `AuthResource.login` valida el cuerpo (400), llama a `LegacyDatabase.findByCredentials(username, password)` y, si devuelve `null`, responde 401 con el mensaje `Invalid user <username> or password`. Si hay éxito responde 200 con `token`, `expiresIn` (3600), `user{username, displayName, role}` y `debug`.
- `LegacyDatabase.findByCredentials` concatena `username` y `password` en el SQL (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`, línea 32). Cualquier excepción JDBC se captura, se imprime y se devuelve `null`, es decir, termina como 401.
- Efecto observado de la concatenación: con `' OR '1'='1` en un solo campo y el otro campo válido, el predicado resultante es verdadero y el usuario se autentica. Con ambos campos manipulados se autentica sin credenciales válidas.
- La base de datos se resuelve con `AUTH_DB_URL` (por defecto `jdbc:sqlite:./data/workshop.db`) y se inicializa con los usuarios `student` y `trainer` en `@PostConstruct`.
- `AuthResourceTest` cubre solo el login exitoso de `student`.
- `docs/ENDPOINTS.md` no existe en el árbol; la baseline de comportamiento es el Issue #23, las specs y el comportamiento actual del código descrito arriba.

## Goals / Non-Goals

**Goals:**

- Que el valor de `username` y `password` nunca se interprete como sintaxis SQL en la consulta de credenciales.
- Que el cambio quede confinado a la capa de acceso a datos de `auth/` y sea revisable de forma independiente.
- Dejar pruebas que fijen el comportamiento protegido antes de tocar la consulta, y una prueba específica de inyección.
- Mantener o superar 85 % de cobertura en el código modificado.

**Non-Goals:**

- No refactorizar `AuthResource.login` (anidamiento, capas), aunque `AGENTS.md` lo recomiende; es un cambio separado.
- No tocar el almacenamiento de contraseñas (hoy en texto plano), el token (`LegacyTokenUtil`), el campo `debug`, el mensaje que refleja `username`, CORS ni la dependencia `commons-text`.
- No cambiar el esquema de la tabla `legacy_users`, los datos semilla ni la gestión de conexiones.
- No modificar `api/` ni `web/`.

## Decisions

### D1. Consulta parametrizada con `PreparedStatement`

`findByCredentials` pasará a usar una sentencia preparada con dos marcadores (`username`, `password`) y asignación de parámetros por posición. La sentencia SQL será una constante sin valores de usuario.

- **Por qué:** es la forma estándar de separar código SQL de datos, está disponible en `java.sql` (sin dependencias nuevas) y lo exige el criterio de aceptación del Issue.
- **Alternativas descartadas:**
  - *Escapar/sanear comillas manualmente:* frágil, depende del motor y no cumple el criterio del Issue.
  - *Lista de caracteres prohibidos en `AuthResource`:* rechazaría contraseñas legítimas con apóstrofes y cambia el contrato (400 en vez de 401).
  - *Introducir ORM o Panache:* amplía el alcance, añade dependencias y rediseña la persistencia.

### D2. Mismo contrato de salida para "no coincide" y para errores

Se conserva el retorno `null` cuando no hay coincidencia, de modo que `AuthResource` sigue produciendo 401 sin `token`. El tratamiento de excepciones JDBC no se modifica en este cambio.

- **Por qué:** la spec exige 401 sin `token` para los intentos de inyección; con parámetros ligados la consulta no falla ni coincide, por lo que el resultado es el mismo camino 401 existente. Cambiar el manejo de errores (por ejemplo a 500) alteraría el contrato y excede el Issue.
- **Alternativa descartada:** lanzar una excepción propia ante errores de BD; mejora la observabilidad, pero cambia códigos de respuesta y debe tratarse en otro cambio.

### D3. Límite del cambio de código

Solo se modifica `LegacyDatabase.findByCredentials` y `AuthResourceTest` (más, si hiciera falta, una clase de prueba nueva bajo `auth/src/test`). `AuthResource`, `LegacyTokenUtil`, `LoginRequest` y `UserRecord` no cambian.

## Contratos protegidos

| Contrato | Fuente | Debe seguir cumpliéndose |
|---|---|---|
| `POST /auth/login` con `student` / `Workshop123!` | Issue, spec | HTTP 200, `user.username = student`, `token` presente |
| Forma de la respuesta 200 | Código actual | Campos `token`, `expiresIn` (3600), `user.username/displayName/role`, `debug` |
| Intento con `' OR '1'='1` (usuario o contraseña) | Issue, spec | HTTP 401 y sin `token` |
| Credenciales inválidas normales | Código actual | HTTP 401 con cuerpo `message` |
| Validación de entrada | Código actual | 400 para cuerpo nulo, usuario vacío o contraseña vacía |
| Usuario `trainer` | Datos semilla | Sigue autenticándose con `Trainer123!` y rol `TRAINER` |
| Ruta, método, media type, CORS y puerto | Código/config | Sin cambios |

## Componentes afectados

- `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`: único archivo funcional modificado (método `findByCredentials`).
- `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`: nuevas pruebas.
- Sin cambios: `AuthResource`, `LegacyTokenUtil`, `LoginRequest`, `UserRecord`, `pom.xml`, `application.properties`, `api/`, `web/`.

## Estrategia incremental

1. **Caracterización (sin tocar código de producción):** añadir pruebas que fijen el comportamiento protegido y verificar que pasan contra el código actual.
2. **Prueba roja de inyección:** añadir los casos de inyección de la spec; deben fallar con el código actual, lo que demuestra la vulnerabilidad.
3. **Cambio mínimo:** parametrizar `findByCredentials` (D1). Ejecutar `mvn test` desde `auth/`.
4. **Verificación:** todas las pruebas en verde y cobertura JaCoCo del código modificado ≥ 85 %.

Cada paso puede ser un commit separado en `feature/h-auth-01`.

## Pruebas de caracterización necesarias

Se escriben y se ejecutan **antes** de modificar la consulta. Ubicación: `auth/src/test/java/...` y ejecución con `mvn test` desde `auth/`.

- Login válido de `student` (existe) y de `trainer`: 200 y campos esperados (`token`, `expiresIn`, `user.username`, `user.role`).
- Contraseña incorrecta con usuario existente: 401 y sin `token`.
- Usuario inexistente: 401 y sin `token`.
- Cuerpo ausente, usuario vacío y contraseña vacía: 400 con su `message`.
- Credenciales legítimas con un apóstrofe (por ejemplo usuario `o'neil` inexistente): 401 sin `token` y sin error 500; fija que un apóstrofe ya no rompe la consulta.

Pruebas de la spec (rojas antes, verdes después):

- `' OR '1'='1` como usuario con contraseña válida: 401 y sin `token`.
- `' OR '1'='1` como contraseña con usuario válido: 401 y sin `token`.
- Ambos campos con `' OR '1'='1`: 401 y sin `token`.

## Risks / Trade-offs

- **[Cambio de comportamiento con apóstrofes]** Antes, un valor con apóstrofe producía error SQL silenciado y 401; ahora se compara literalmente y también da 401 si no coincide. → Cubierto por la prueba de apóstrofe; el resultado externo no cambia.
- **[Base SQLite compartida entre pruebas]** Las pruebas usan `./data/workshop.db` por defecto y los datos semilla persisten. → Las pruebas no escriben datos y dependen solo de `student`/`trainer`; si se necesita aislamiento, usar un `AUTH_DB_URL` de prueba sin secretos reales.
- **[Falsa sensación de cierre]** El Issue arregla solo la inyección; contraseñas en texto plano, `debug` y el reflejo de `username` en el 401 siguen presentes. → Quedan registrados como no objetivos para hallazgos posteriores.
- **[Cobertura]** Un cambio pequeño puede dejar ramas sin cubrir (error de conexión). → Las pruebas de la estrategia cubren éxito, no coincidencia e inyección; si JaCoCo marca ramas modificadas sin cubrir, añadir un caso específico, no excluirlas.

## Migration Plan / Rollback

- No hay migración de datos, esquema ni configuración.
- **Rollback:** revertir el commit que modifica `LegacyDatabase.findByCredentials` (`git revert`), conservando las pruebas de caracterización. Las pruebas de inyección fallarán de nuevo, lo que es el comportamiento esperado de la versión vulnerable y debe tratarse como bloqueo de despliegue.
- No requiere pasos en `api/` ni `web/`.
