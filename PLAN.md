# Plan de corrección

## Web
###aprobacion humana
- George
- 2026/10/26
- H-WEB-01,H-WEB-02,H-WEB-03,H-WEB-04,H-WEB-05,H-WEB-06
- Aprobación registrada para estos seis IDs. No se encontró aprobación humana explícita para H-WEB-07 ni H-WEB-08; no implementar esos hallazgos sin confirmación.

### Selección y restricciones comunes

Se seleccionan H-WEB-01 a H-WEB-06 porque las seis filas están en `HALLAZGOS.md` con estado `Pendiente`. H-WEB-01, H-WEB-02, H-WEB-03, H-WEB-05 y H-WEB-06 tienen evidencia directa del comportamiento o de la cobertura actual. H-WEB-04 se incluye como verificación condicionada: las versiones están presentes, pero no hay evidencia de CVE aplicable.

No existe `docs/ENDPOINTS.md`; se conserva el contrato observado en `HALLAZGOS.md`: `POST http://localhost:8080/auth/login` con `username`, `password` y `client`; `GET http://localhost:8000/api/tasks?owner=<username>` con Bearer; filtro de tareas archivadas, etiqueta y orden actual; login navega a dashboard y logout vuelve a login. No cambiar esos endpoints, payloads ni encabezados.

Las pruebas de caracterización se agregan antes de modificar componentes o configuración. Ejecutar desde `web/` con `npm test`; `npm run test:coverage` queda como comprobación posterior. Ninguno de esos comandos se ha ejecutado en esta planificación.

### H-WEB-01 — Token de sesión en `localStorage`

- **Hallazgo:** token de sesión en almacenamiento persistente del navegador; estado `Pendiente` en `HALLAZGOS.md`.
- **Problema:** cualquier JavaScript ejecutado en el mismo origen puede leer el token. Un cambio de almacenamiento exclusivamente frontend no elimina el acceso desde JavaScript.
- **Cambio propuesto:** centralizar lectura, escritura y borrado en `SessionService`, sin cambiar el almacenamiento mientras no se elija una alternativa. No se moverá una credencial a otro mecanismo frontend por defecto: `sessionStorage` seguiría accesible a JavaScript y cambiaría la persistencia entre recargas/cierre de pestaña. Una cookie `HttpOnly` requiere coordinación y cambios backend fuera de este alcance.
- **Archivos a tocar:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`; nuevo `web/src/app/session/session.service.ts`; pruebas de login, dashboard y sesión. El almacenamiento de preferencias puede permanecer en `localStorage` porque no es la credencial.
- **Caracterización y resultado:** las pruebas verifican login válido, persistencia en `localStorage`, carga con Bearer, acceso sin token y logout. La sesión actualmente persiste en `localStorage`. No se aplicó cambio de almacenamiento; H-WEB-01 permanece pendiente hasta acordar solución compatible con el backend y el modelo de amenazas.

### H-WEB-02 — Componentes acoplados a HTTP, sesión y navegación

- **Hallazgo:** login y dashboard conocen URLs, transporte HTTP, almacenamiento y navegación; estado `Pendiente`.
- **Problema:** responsabilidades mezcladas hacen más difícil probar flujos y cambiar transporte o configuración sin editar componentes.
- **Cambio propuesto:** introducir `AuthService` para login, `TasksService` para consulta de tareas y reutilizar `SessionService` para sesión. Los componentes conservan validación/presentación y navegación; centralizar URLs en configuración por ambiente según `docs/GOOD_PRACTICES.md`. No agregar dependencias: reutilizar Angular/Axios ya instalados y coordinar el transporte para no duplicar clientes.
- **Archivos a tocar:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`; nuevos `web/src/app/services/auth.service.ts`, `web/src/app/services/tasks.service.ts`, `web/src/app/session/session.service.ts` y `web/src/environments/environment.ts`; configuración de build solo si se incorpora un reemplazo por ambiente; pruebas de los servicios y componentes.
- **Caracterización previa:** verificar con mocks que el login realiza el mismo POST, con mismo cuerpo y timeout, que una respuesta con token guarda sesión y navega; que el dashboard realiza el mismo GET con `owner` y Bearer, excluye `ARCHIVED`, mantiene etiquetas/orden y presenta estado de error; que logout borra sesión y vuelve a login.
- **Resultado:** `AuthService`, `TasksService` y `SessionService` separan HTTP y persistencia; las URLs quedaron en `web/src/environments/environment.ts`. Se conservaron los contratos observados y los errores de login/tareas usan mensajes genéricos; caracterización y regresión pasan.

### H-WEB-03 — Mensaje dinámico con `[innerHTML]`

- **Hallazgo:** mensaje compuesto con usuario y error, enlazado como HTML; estado `Pendiente`. Angular sanitiza por defecto el binding actual, por lo que no se asume XSS confirmado.
- **Problema:** no se requiere HTML para mostrar el error y mantenerlo crea una superficie evitable para inyección de marcado o futuros usos inseguros.
- **Cambio propuesto:** representar mensajes como texto plano y usar interpolación (`{{ message }}`), retirando las etiquetas HTML embebidas de los strings. Mantener mensajes comprensibles para validación, respuesta sin token y fallo de login; no mostrar HTML de respuesta.
- **Archivos a tocar:** `web/src/app/login/login.component.ts`, `web/src/app/login/login.component.html` y pruebas de login.
- **Caracterización previa:** cubrir usuario/contraseña vacíos, respuesta sin token y fallo HTTP; verificar el texto mostrado y que el nombre ingresado y el error se tratan como contenido, no como estructura HTML. La configuración Vitest actual es `node` y no ofrece un entorno DOM: antes de exigir una prueba de renderizado, confirmar si el harness disponible permite probar la plantilla; no añadir una dependencia sin justificarla.
- **Resultado:** la plantilla usa interpolación de texto, los errores se muestran con mensajes genéricos y no se enlaza HTML del usuario/backend. Las pruebas inspeccionan que no exista el binding `innerHTML` y que los detalles backend no se expongan; no se agregó dependencia de DOM.

### H-WEB-04 — Versiones de `axios` y `lodash` por verificar

- **Hallazgo:** `axios` 0.31.0 y `lodash` 4.17.21 están fijados; aplicabilidad de advisories no comprobada; estado `Pendiente`.
- **Problema:** sin auditoría no se puede concluir que exista una vulnerabilidad ni elegir una versión correctiva con evidencia.
- **Cambio realizado:** `npm audit` reportó advisories aplicables a Axios 0.31.0 y Lodash 4.17.21. Axios se actualizó a 1.20.0; se retiraron Lodash y `@types/lodash`, sustituyendo su merge de preferencias planas por spread tipado. No se ejecutó `npm audit fix --force`.
- **Archivos tocados:** `web/package.json`, `web/package-lock.json`, `web/src/app/login/login.component.ts` y las pruebas de login/preferencias.
- **Resultado y riesgo:** la auditoría posterior no lista Axios ni Lodash como vulnerables; todavía informa 23 advisories en otras dependencias transitivas/toolchain, incluidos 6 críticos. Además, `npm ci --dry-run` estándar falla por ocho paquetes ausentes del lockfile; con `--legacy-peer-deps` pasa. H-WEB-04 vuelve a `Pendiente` hasta regenerar y validar un lockfile que permita instalación limpia estándar.

### H-WEB-05 — `any` y validación anidada; duplicación no confirmada

- **Hallazgo:** `any` en estado/respuestas/tareas y condiciones anidadas en login; no se confirmó duplicación; estado `Pendiente`.
- **Problema:** `any` evita detectar incompatibilidades de request/response y datos de tareas; la anidación dificulta seguir los casos de validación. No extraer código por duplicación sin evidencia adicional.
- **Cambio propuesto:** definir tipos para request/response de login, usuario, preferencias y tarea; reemplazar `any` por esos tipos y usar retornos anticipados en la validación. Mantener funciones pequeñas por responsabilidad y extraer solo lógica que las pruebas o una revisión identifiquen como repetida.
- **Archivos a tocar:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`, `web/src/app/utils/legacy-format.ts`; nuevos modelos bajo `web/src/app/models/`; pruebas correspondientes.
- **Caracterización previa:** capturar validaciones de usuario y contraseña vacíos, respuesta correcta y sin token, errores de login/carga, campos opcionales usados por `formatTaskLabel`, filtro de archivadas y orden por prioridad. Las pruebas deben fijar el comportamiento antes de cambiar tipos o estructura.
- **Resultado:** los componentes, respuestas, preferencias y tareas usan tipos; login usa retornos anticipados. No se encontró ni extrajo duplicación sin evidencia. La caracterización mantiene el orden que realmente producía el comparador original (`Low`, `High` para los datos de prueba).

### H-WEB-06 — Pruebas observadas limitadas a una utilidad

- **Hallazgo:** solo se encontró una especificación para `formatTaskLabel`; estado `Pendiente`.
- **Problema:** los flujos de autenticación, persistencia de sesión, dashboard y logout no tienen regresión automatizada observada.
- **Cambio propuesto:** añadir pruebas focalizadas de flujo con Vitest y mocks, empezando por caracterización antes de refactorizar. Mantener las pruebas unitarias sin depender de servicios reales ni credenciales reales. La prueba de renderizado de plantilla requiere resolver la limitación del entorno `node` anotada en H-WEB-03.
- **Archivos a tocar:** nuevo `web/src/app/login/login.component.spec.ts`, nuevo `web/src/app/dashboard/dashboard.component.spec.ts`, y especificaciones de servicios/modelos que se incorporen por H-WEB-01, H-WEB-02 y H-WEB-05. No modificar `web/vitest.config.ts` salvo que se justifique un harness compatible y se acuerde su dependencia/configuración.
- **Caracterización previa:** cubrir login válido e inválido, token ausente, respuesta sin token, manejo de error, carga con/sin sesión, filtro y orden de tareas, y logout. Ejecutar `npm test` en `web/` y registrar después resultados y cobertura; no se afirma que hayan pasado.
- **Resultado:** se añadieron pruebas de login, preferencias, dashboard, sesión, logout, API errors y formato. `npm test` final pasa 15/15; cobertura V8 global 86.78%. Los archivos de producción modificados quedaron en o sobre el 85%: login 96.72%, dashboard 100%, servicios/sesión 100%, `api-error.ts` 100%, `legacy-format.ts` 100% y configuración 100%.

## Dependencias y decisiones pendientes

- La aprobación humana para H-WEB-01 a H-WEB-06 está registrada al inicio de este apartado, por George el 2026-10-26.
- La pregunta para cambiar persistencia a `sessionStorage` se omitió. Se conserva `localStorage`; H-WEB-01 permanece pendiente y no se afirma que centralizar el acceso resuelva el riesgo de exposición a JavaScript/XSS.
- No se movieron secretos a otra parte del frontend ni se cambió el backend.
- Desviación acotada del plan: durante la revisión se detectó que devolver `message`/`detail` crudos del backend contradecía la guía de errores genéricos. `getApiErrorMessage` ahora usa el fallback genérico; pruebas verifican que no se muestren los detalles.
- La auditoría confirma que los advisories directos de Axios/Lodash se atendieron. Quedan 23 advisories transitivos/toolchain fuera de este alcance; no se ejecutó `npm audit fix --force`.
- H-WEB-02, H-WEB-03, H-WEB-05 y H-WEB-06 están implementados. H-WEB-01 sigue pendiente por la decisión de persistencia; H-WEB-04 vuelve a pendiente por el lockfile; H-WEB-07 y H-WEB-08 son hallazgos nuevos de la revisión local y no están aprobados para implementación.

## Revisión local contra main

- H-WEB-04 se reabrió: desde `web/`, `npm ci --dry-run --ignore-scripts` falla porque faltan `webpack`, `@emnapi/core`, `@emnapi/runtime`, `@emnapi/wasi-threads`, `es-module-lexer`, `minimizer-webpack-plugin`, `watchpack` y `terser`. El mismo dry-run con `--legacy-peer-deps` termina correctamente; no se debe exigir esa opción sin documentarla como configuración del proyecto.
- Para H-WEB-04 se añadió `web/.npmrc` con `legacy-peer-deps=true`; `npm ci --dry-run --ignore-scripts` estándar pasa con esa configuración. La instalación real `npm ci --ignore-scripts` no pudo completarse: Windows devolvió `EPERM` al intentar retirar `web/node_modules/@esbuild/win32-x64/esbuild.exe`, que estaba en uso por `ng serve`. No marcar resuelto hasta repetir instalación limpia y pruebas tras cerrar el servidor.
- H-WEB-07 y H-WEB-08 permanecen pendientes y sin aprobación humana verificable; la línea de aprobación anterior que los incluía se corrigió para no atribuir decisiones no registradas.
- H-WEB-07: `LoginComponent` escribe el AxiosError completo en consola tras un fallo; el request contiene `password`. No se verificó mediante una llamada real y se registra como riesgo estático de posible exposición del config/body.
- H-WEB-08: `main` aceptaba la respuesta si tenía `data.token`; la versión revisada requiere también `user`. No hay `docs/ENDPOINTS.md` ni test para token sin user, por lo que queda pendiente confirmar el contrato de respuesta antes de cerrar compatibilidad.
- En la prueba de login el template se lee como texto; no se monta en DOM ni se verifica comportamiento con lector de pantalla. La interpolación evita el binding `[innerHTML]`, pero falta prueba de accesibilidad/lectura dinámica.

## Registro de ejecuciones

| fecha | componente e IDs | comando/acción | resultado |
|---|---|---|---|
| 2026-10-26 | web; H-WEB-01, H-WEB-02, H-WEB-03, H-WEB-05, H-WEB-06 | `npm test` desde `web/`, caracterización inicial | Falló antes de ejecutar dos suites porque faltaba cargar `@angular/compiler` en Vitest Node. |
| 2026-10-26 | web; H-WEB-02, H-WEB-05, H-WEB-06 | `npm test` desde `web/`, tras cargar el compilador | 10/11 pruebas pasaron; la expectativa de orden no coincidía con el comparador actual. Se corrigió la expectativa para reflejar el comportamiento observado (`Low`, `High`), sin cambiar producción. |
| 2026-10-26 | web; H-WEB-01, H-WEB-02, H-WEB-03, H-WEB-05, H-WEB-06 | `npm test` desde `web/`, caracterización corregida | 3 archivos de prueba y 11/11 pruebas pasaron antes de cambios de producción. |
| 2026-10-26 | web; H-WEB-04 | `npm audit --audit-level=moderate` desde `web/` | Salida 1: 25 advisories en el árbol instalado; confirmó avisos para Axios y Lodash, además de Angular/Vitest y dependencias transitivas. `npm audit fix --force` no se ejecutó por proponer cambios fuera del alcance. |
| 2026-10-26 | web; H-WEB-04 | `npm view axios version` y `npm view lodash version` desde `web/` | El registro devolvió Axios 1.20.0 y Lodash 4.18.1; se instaló Axios 1.20.0 y se retiró Lodash después de confirmar su sustitución en pruebas. |
| 2026-10-26 | web; H-WEB-03, H-WEB-06 | `npm test` desde `web/`, tras agregar caracterización del binding | 3 archivos y 12/12 pruebas pasaron antes de cambios de producción del mensaje. |
| 2026-10-26 | web; H-WEB-02, H-WEB-03, H-WEB-05, H-WEB-06 | `npm test` desde `web/`, tras el slice de login | 3 archivos y 12/12 pruebas pasaron; POST, storage y navegación conservaron lo observado, y la prueba comprueba interpolación sin `[innerHTML]`. |
| 2026-10-26 | web; H-WEB-02, H-WEB-05, H-WEB-06 | `npm test` desde `web/`, tras el slice de dashboard | 3 archivos y 12/12 pruebas pasaron; GET, Bearer, filtro, orden y logout conservados. |
| 2026-10-26 | web; H-WEB-04 | `npm install --save-exact axios@1.20.0` desde `web/` | Falló por error interno de npm al resolver peers (`Cannot read properties of null (reading 'children')`); manifiesto y lockfile seguían sin cambios. |
| 2026-10-26 | web; H-WEB-04 | `npm install --save-exact axios@1.20.0 --legacy-peer-deps --ignore-scripts` desde `web/` | Axios actualizado; npm reportó 20 advisories en el árbol. No se usó `--force`. |
| 2026-10-26 | web; H-WEB-04 | `npm test` desde `web/`, después de actualizar Axios | 3 archivos y 12/12 pruebas pasaron. |
| 2026-10-26 | web; H-WEB-04 | `npm uninstall lodash @types/lodash --legacy-peer-deps --ignore-scripts` desde `web/` | Dependencias retiradas; npm reportó 19 advisories en ese momento. |
| 2026-10-26 | web; H-WEB-04, H-WEB-05, H-WEB-06 | `npm test` desde `web/`, después de retirar Lodash | 3 archivos y 12/12 pruebas pasaron, incluida la combinación tipada de preferencias. |
| 2026-10-26 | web; H-WEB-04 | `npm audit --audit-level=moderate` desde `web/`, auditoría posterior | Salida 1: 23 advisories restantes en Angular/Vitest/Vite y dependencias transitivas; Axios y Lodash no aparecen en el reporte. |
| 2026-10-26 | web; H-WEB-05, H-WEB-06 | `npm test` desde `web/`, tras cubrir ramas de errores y etiquetas | 4 archivos y 16/16 pruebas pasaron. |
| 2026-10-26 | web; H-WEB-02, H-WEB-03, H-WEB-05, H-WEB-06 | `npm run test:coverage` desde `web/` | 16/16 pruebas pasaron; cobertura global 86.58% statements/lines y 88.7% branches; todos los archivos de producción modificados alcanzaron ≥85%. |
| 2026-10-26 | web; H-WEB-02, H-WEB-03, H-WEB-04, H-WEB-05, H-WEB-06 | `npm run build` desde `web/` | Build Angular de producción completado correctamente. |
| 2026-10-26 | web; H-WEB-02, H-WEB-03, H-WEB-06 | `npm test` desde la raíz por cwd incorrecto | Falló con ENOENT porque no hay `package.json` en la raíz; no se modificó código. Se repitió desde `web/`. |
| 2026-10-26 | web; H-WEB-02, H-WEB-03, H-WEB-06 | `npm test` desde `web/`, mensajes genéricos | 4 archivos y 15/15 pruebas pasaron; los detalles backend no se exponen. |
| 2026-10-26 | web; H-WEB-02, H-WEB-03, H-WEB-05, H-WEB-06 | `npm run test:coverage` desde `web/`, resultado final | 15/15 pruebas; cobertura global 86.78% statements/lines, 88.46% branches; todos los archivos de producción modificados ≥85%. |
| 2026-10-26 | web; H-WEB-02, H-WEB-03, H-WEB-05 | `npm run build` desde `web/`, resultado final | Build Angular de producción completado correctamente. |
| 2026-10-26 | web; H-WEB-04 | `npm ci --dry-run --ignore-scripts` desde la raíz por cwd incorrecto | Falló porque no había lockfile en la raíz; sin cambios. Se repitió en `web/`. |
| 2026-10-26 | web; H-WEB-04 | `npm ci --dry-run --ignore-scripts` desde `web/` | Falló por ocho entradas ausentes en `package-lock.json`; lockfile no coincide con el árbol requerido. |
| 2026-10-26 | web; H-WEB-01, H-WEB-02, H-WEB-03, H-WEB-05, H-WEB-06 | `npm test` desde `web/`, caracterización de esta ejecución | 4 archivos y 15/15 pruebas pasaron antes de intentar instalación limpia. |
| 2026-10-26 | web; H-WEB-04 | `npm ci --dry-run --ignore-scripts` desde `web/`, antes de añadir `.npmrc` | Falló por ocho entradas ausentes del lockfile. |
| 2026-10-26 | web; H-WEB-04 | `npm install --package-lock-only --ignore-scripts` desde `web/` | Falló con error interno de npm (`Cannot read properties of null (reading 'children')`); no sincronizó el lockfile. |
| 2026-10-26 | web; H-WEB-04 | `npm install --package-lock-only --legacy-peer-deps --ignore-scripts` y con `--include=optional` | Ambas terminaron “up to date”; no agregaron las entradas faltantes para la instalación estándar. Auditoría npm reportó 19 vulnerabilidades (7 moderadas, 7 altas, 5 críticas). |
| 2026-10-26 | web; H-WEB-04 | `npm ci --dry-run --ignore-scripts` después de añadir `web/.npmrc` | Terminó correctamente con configuración local `legacy-peer-deps=true`. |
| 2026-10-26 | web; H-WEB-04 | `npm ci --ignore-scripts` desde `web/` | No completó: Windows devolvió `EPERM` al eliminar `@esbuild/win32-x64/esbuild.exe`, en uso por un proceso `ng serve` preexistente. |
| 2026-10-26 | web; H-WEB-04, H-WEB-06 | `npm test` después del `npm ci` interrumpido | No ejecutó pruebas: `vitest` ya no estaba disponible tras la instalación parcial. Requiere restaurar dependencias luego de liberar el ejecutable. |
| 2026-10-26 | web; H-WEB-04 | `npm ci --dry-run --legacy-peer-deps --ignore-scripts` desde `web/` | Terminó correctamente antes y después de registrar la opción en `.npmrc`. |
