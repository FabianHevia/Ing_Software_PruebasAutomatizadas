*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${BROWSER}        Chrome
${URL}            http://127.0.0.1:5000/register
${USERNAME}       valid_username
${EMAIL}          valid_email@example.com  # Asigna un email válido
${PASSWORD}       valid_password

*** Test Cases ***
Prueba de Registro Exitoso
    Abrir Navegador y Navegar a Registro
    Ingresar Credenciales Válidas y Enviar
    Verificar Redireccionamiento a Menu
    Cerrar Navegador

*** Keywords ***
Abrir Navegador y Navegar a Registro
    Open Browser    ${URL}    ${BROWSER}
    Title Should Be    Página de Inicio 

Ingresar Credenciales Válidas y Enviar
    Input Text    id=username    ${USERNAME}
    Input Text    id=email       ${EMAIL}
    Input Text    id=password    ${PASSWORD}
    Input Text    id=confirm_password    ${PASSWORD}
    Click Button    xpath=//button[text()='Register']  # Ajustar según la forma en que hayas definido el botón

Verificar Redireccionamiento a Menu
    Location Should Be    http://127.0.0.1:5000/menu
    Title Should Be    Menú Principal

Cerrar Navegador
    Close Browser


