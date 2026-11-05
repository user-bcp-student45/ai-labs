package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.response.ValidatableResponse;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

@QuarkusTest
class AuthResourceTest {
    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("user.role", is("STUDENT"))
                .body("expiresIn", is(3600))
                .body("token", notNullValue());
    }

    // Contrato protegido: usuario sembrado `trainer` sigue autenticandose con su rol.
    @Test
    void logsInWithTrainerUser() {
        postLogin("{\"username\":\"trainer\",\"password\":\"Trainer123!\"}")
                .statusCode(200)
                .body("token", notNullValue())
                .body("expiresIn", is(3600))
                .body("user.username", is("trainer"))
                .body("user.role", is("TRAINER"));
    }

    // Contrato protegido: credenciales invalidas normales -> 401 con `message` y sin `token`.
    @Test
    void rejectsWrongPasswordForExistingUser() {
        postLogin("{\"username\":\"student\",\"password\":\"wrong-password\"}")
                .statusCode(401)
                .body("message", is("Invalid user student or password"))
                .body("token", nullValue());
    }

    @Test
    void rejectsUnknownUser() {
        postLogin("{\"username\":\"ghost\",\"password\":\"Workshop123!\"}")
                .statusCode(401)
                .body("message", is("Invalid user ghost or password"))
                .body("token", nullValue());
    }

    // Contrato protegido: validacion de entrada -> 400 con `message`.
    @Test
    void rejectsMissingBody() {
        given()
                .contentType("application/json")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Request is null"));
    }

    @Test
    void rejectsEmptyUsername() {
        postLogin("{\"username\":\"\",\"password\":\"Workshop123!\"}")
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsEmptyPassword() {
        postLogin("{\"username\":\"student\",\"password\":\"\"}")
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    // Contrato protegido: un apostrofe en el usuario no produce 500 ni autentica; sigue siendo 401.
    @Test
    void rejectsUnknownUserWithApostropheWithoutServerError() {
        postLogin("{\"username\":\"o'neil\",\"password\":\"Workshop123!\"}")
                .statusCode(401)
                .body("message", is("Invalid user o'neil or password"))
                .body("token", nullValue());
    }

    // Spec "Las credenciales de inyeccion no autentican" (Issue #23): rojas hasta parametrizar la consulta.
    @Test
    void rejectsInjectionStringAsUsernameWithValidPassword() {
        postLogin("{\"username\":\"' OR '1'='1\",\"password\":\"Workshop123!\"}")
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void rejectsInjectionStringAsPasswordWithValidUsername() {
        postLogin("{\"username\":\"student\",\"password\":\"' OR '1'='1\"}")
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void rejectsInjectionStringInBothFields() {
        postLogin("{\"username\":\"' OR '1'='1\",\"password\":\"' OR '1'='1\"}")
                .statusCode(401)
                .body("token", nullValue());
    }

    private static ValidatableResponse postLogin(String jsonBody) {
        return given()
                .contentType("application/json")
                .body(jsonBody)
                .when().post("/auth/login")
                .then();
    }
}
