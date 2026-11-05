# Spec Delta

## Purpose

Define el comportamiento observable del inicio de sesión de auth, preservando el acceso válido y evitando que valores de credenciales alteren el resultado de autenticación.

## ADDED Requirements

### Requirement: El inicio de sesión válido conserva su respuesta
El sistema SHALL aceptar las credenciales válidas del usuario `student` y preservar la respuesta exitosa de `POST /auth/login`.

#### Scenario: Inicio de sesión válido de student
- **WHEN** se envía `student` como usuario y `Workshop123!` como contraseña a `POST /auth/login`
- **THEN** el endpoint responde HTTP 200, `user.username` es `student` y `token` está presente

### Requirement: Las credenciales de inyección no autentican
El sistema SHALL tratar los valores de usuario y contraseña como credenciales inválidas cuando contienen la cadena `' OR '1'='1`, sin autenticar la solicitud.

#### Scenario: Cadena de inyección en el usuario
- **WHEN** se envía `' OR '1'='1` como usuario a `POST /auth/login`
- **THEN** el endpoint responde HTTP 401 y la respuesta no contiene `token`

#### Scenario: Cadena de inyección en la contraseña
- **WHEN** se envía `' OR '1'='1` como contraseña a `POST /auth/login`
- **THEN** el endpoint responde HTTP 401 y la respuesta no contiene `token`