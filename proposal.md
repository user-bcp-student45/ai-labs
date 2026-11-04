**📄 Archivo: `proposal.md`**

**Proposal (ya escrito, no se modifica)**

- **Por qué:** hoy el cliente que pierde su tarjeta debe llamar al centro de atención. Un bloqueo inmediato desde la app reduce el riesgo de fraude mientras decide si la reporta como perdida.
- **Qué cambia:** el cliente puede bloquear y desbloquear su tarjeta de forma temporal desde la app.
- **Alcance:** tarjetas de débito y crédito del propio cliente. Quedan fuera el bloqueo definitivo, la reposición y el reporte de robo.
- **Cómo se sabrá que está hecho:** los criterios de las specs pasan en las pruebas.

**📄 Archivo: `specs/tarjetas/spec.md`**

**Specs (completar al menos 3 criterios verificables)**

1. Si el cliente solicita el bloqueo/desbloqueo, el sistema bloqueará temporalmente por un día la tarjeta y te mostrará información de la operación mediante el correo registrado.
2. Mientras la tarjeta está bloqueada, no te debe permitir realizar operaciones que involucren la tarjeta bloqueada. (consulta de movimientos, transferencias, pagos)
3. Luego de que pase el día de bloqueo temporal, la tarjeta se deberá desbloquear, a menos que el cliente no lo haya desbloqueado previamente.
4. Si el cliente solicita Bloquear/desbloquear su tarjeta, el sistema deberá solicitar el token digital para completar la operación.

**📄 Archivo: `design.md`**

**Decisiones de diseño**

- Antes de bloquear o desbloquear una tarjeta, el sistema valida que pertenece al cliente autenticado.
- El estado de bloqueo temporal se gestiona por tarjeta y se verifica antes de ejecutar cada operación.
- La aplicación muestra una confirmación clara cuando la operación termina correctamente y un mensaje de error cuando no puede completarse.
- Los datos sensibles del cliente no deben aparecer en los logs ni en los mensajes de error.

---

**📄 Archivo: `tasks.md`**

**Lista de tareas (pasos a ejecutar, para ir marcando)**

- [ ] Implementar la validación de propiedad de la tarjeta antes de bloquearla o desbloquearla.
- [ ] Implementar el bloqueo temporal de tarjetas propias activas.
- [ ] Impedir nuevas compras con tarjetas bloqueadas temporalmente.
- [ ] Implementar el desbloqueo de tarjetas bloqueadas temporalmente.
- [ ] Mostrar mensajes de confirmación o error según el resultado de la operación.
- [ ] Crear pruebas automáticas para verificar los criterios 1, 2 y 3.
- [ ] Crear pruebas automáticas para verificar que las solicitudes sobre tarjetas ajenas se rechazan y no modifican su estado.
- [ ] Verificar que los logs y mensajes de error no exponen datos sensibles.