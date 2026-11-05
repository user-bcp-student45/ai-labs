# Proposal

## Why

El Issue #23 (`user-bcp-student45/ai-labs#23`) identifica que valores de credenciales pueden alterar la consulta de autenticación y permitir un inicio de sesión no autorizado. Resolverlo protege la frontera de autenticación sin cambiar la experiencia de inicio de sesión válida.

## What Changes

- **En alcance:** especificar el comportamiento de `POST /auth/login` para credenciales válidas y para valores con sintaxis de inyección en usuario o contraseña.
- **Fuera de alcance:** cambios en `api/` o `web/`, otros flujos de autenticación, cambios al formato de respuesta, al manejo de tokens o a la validación de campos no descritos por el issue.
- **Comportamiento a preservar:** las credenciales `student` / `Workshop123!` siguen produciendo HTTP 200 con `user.username` igual a `student` y un `token` presente.
- **Comportamiento requerido por el issue:** un intento con `' OR '1'='1` como usuario o contraseña produce HTTP 401 y no devuelve `token`.

El documento de baseline indicado, `docs/ENDPOINTS.md`, no existe en el árbol consultado. Por ello, esta propuesta no afirma haberlo contrastado; toma como contrato disponible los criterios explícitos del Issue #23, que pide conservar el inicio de sesión válido y no indica cambios en la ruta ni en la respuesta exitosa.

## Capabilities

### New Capabilities
- `auth-login`: comportamiento observable del inicio de sesión y rechazo de credenciales que intentan alterar la autenticación.

### Modified Capabilities
- Ninguna. El inventario OpenSpec no contiene capacidades existentes.

## Impact

- Componente y pruebas: `auth/` únicamente.
- Endpoint existente: `POST /auth/login`; se preservan la respuesta exitosa documentada por el issue y el formato de rechazo HTTP 401 sin token para el caso de inyección.
- Issue de referencia: #23, “H-AUTH-01 Usar consultas parametrizadas en el login de auth”.