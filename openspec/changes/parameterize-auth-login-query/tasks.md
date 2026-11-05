# Tasks

Issue de referencia: `user-bcp-student45/ai-labs#23`. Alcance: solo `auth/`. Las pruebas se ejecutan con `mvn test` desde `auth/`; Git y OpenSpec, desde la raíz de `ai-labs`, en la rama `feature/h-auth-01`.

## 1. Pruebas de caracterización (sin tocar código de producción)

- [x] 1.1 Ejecutar `mvn test` en `auth/` y verificar que la línea base (`AuthResourceTest.logsInWithWorkshopUser`) pasa antes de cambiar nada
- [x] 1.2 Añadir en `AuthResourceTest` el login válido de `trainer` / `Trainer123!` y verificar que pasa contra el código actual con 200, `token`, `expiresIn` = 3600, `user.username` = `trainer` y `user.role` = `TRAINER`
- [x] 1.3 Reforzar la prueba de `student` con `expiresIn` = 3600 y `user.role` = `STUDENT`, y verificar que pasa contra el código actual
- [x] 1.4 Añadir pruebas de credenciales inválidas (contraseña incorrecta con usuario existente; usuario inexistente) y verificar que pasan con 401, cuerpo `message` y sin `token`
- [x] 1.5 Añadir pruebas de validación de entrada (cuerpo ausente, usuario vacío, contraseña vacía) y verificar que pasan con 400 y su `message`
- [x] 1.6 Añadir la prueba de un usuario con apóstrofe (`o'neil`, inexistente) y verificar que pasa con 401, sin `token` y sin 500
- [x] 1.7 Ejecutar `mvn test` en `auth/` y verificar que toda la caracterización está en verde antes de continuar

## 2. Pruebas de la spec en rojo

- [x] 2.1 Añadir la prueba `' OR '1'='1` como usuario con contraseña válida (`Workshop123!`) esperando 401 y sin `token`
- [x] 2.2 Añadir la prueba `' OR '1'='1` como contraseña con usuario válido (`student`) esperando 401 y sin `token`
- [x] 2.3 Añadir la prueba con `' OR '1'='1` en ambos campos esperando 401 y sin `token`
- [x] 2.4 Ejecutar `mvn test` en `auth/` y verificar que fallan exactamente las pruebas de 2.1 a 2.3 (evidencia de la vulnerabilidad) y que las del grupo 1 siguen en verde; no se aceptan fallos adicionales

## 3. Cambio funcional incremental

- [x] 3.1 En `LegacyDatabase.findByCredentials`, reemplazar la concatenación por una sentencia SQL constante con dos marcadores y asignar `username` y `password` como parámetros; verificar con `git diff` que el SQL no contiene valores de entrada
- [x] 3.2 Mantener el retorno `null` cuando no hay coincidencia y el manejo de excepciones actual; verificar con `git diff` que `AuthResource` y el resto de archivos fuera de `LegacyDatabase.java` y las pruebas no cambiaron
- [x] 3.3 Ejecutar `mvn test` en `auth/` y verificar que pasan las pruebas de los grupos 1 y 2, incluido el login válido de `student` con 200, `user.username` y `token`

## 4. Verificación final

- [x] 4.1 Ejecutar `mvn verify` en `auth/` y verificar en el informe JaCoCo que la cobertura del código modificado es 85 % o superior, sin excluir clases ni ramas
- [x] 4.2 Ejecutar `git status` y `git diff --stat` desde la raíz y verificar que los cambios de código están solo en `auth/` y los de planificación solo en `openspec/changes/parameterize-auth-login-query/`
- [x] 4.3 Ejecutar `openspec validate "parameterize-auth-login-query"` desde la raíz y verificar que el cambio es válido
- [x] 4.4 Comprobar uno a uno los criterios de aceptación del Issue #23 contra los resultados de las pruebas y registrar el resultado en la descripción del cambio al presentarlo para revisión

## Workflow follow-up

- Revisión y aprobación humanas antes de integrar, según `AGENTS.md`.
- Archivar el cambio OpenSpec una vez cumplidos los requisitos de revisión del proyecto.
