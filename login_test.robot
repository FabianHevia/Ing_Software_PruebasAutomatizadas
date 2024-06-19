*** Settings ***
Documentation     Prueba de Login desde index.html a menu.html
Library           SeleniumLibrary

*** Variables ***
${BROWSER}        Chrome
${URL}            http://localhost/index.html
${USERNAME}       admin
${PASSWORD}       1234

*** Test Cases ***
Prueba de Login
    Abrir Navegador y Navegar a Index
    Ingresar Credenciales y Enviar
    Verificar Redireccionamiento a Menu
    Cerrar Navegador

*** Keywords ***
Abrir Navegador y Navegar a Index
    Open Browser    ${URL}    ${BROWSER}
    Title Should Be    Página de Inicio

Ingresar Credenciales y Enviar
    Input Text    id=username    ${USERNAME}
    Input Text    id=password    ${PASSWORD}
    Click Button    id=login-button

Verificar Redireccionamiento a Menu
    Location Should Be    http://localhost/menu.html
    Title Should Be    Menú Principal

Cerrar Navegador
    Close Browser