*** Settings ***
Documentation     Pruebas para el registro y visualización de propiedades en la Vista de Propiedades
Library           SeleniumLibrary

*** Variables ***
${BROWSER}        Chrome
${URL}            http://127.0.0.1:5000/
${USERNAME}       agustinikus
${PASSWORD}       amparo12
${DIRECCION}      Calle Falsa 123
${COMUNA}         Springfield
${IMAGEN_PATH}    ${CURDIR}/test_image.jpg

*** Test Cases ***
Prueba de Registro de Propiedad
    [Documentation]    Este caso prueba el registro de una nueva propiedad y verifica que aparece en la lista.
    Iniciar Sesión
    Navegar a Vista de Propiedades
    Registrar Nueva Propiedad
    Verificar Propiedad Registrada
    Cerrar Navegador

*** Keywords ***
Iniciar Sesión
    Open Browser    ${URL}    ${BROWSER}
    Title Should Be    Página de Inicio
    Input Text    id=username    ${USERNAME}
    Input Text    id=password    ${PASSWORD}
    Click Button    id=login-button
    Location Should Be    ${URL}menu
    Title Should Be    Menú Principal

Navegar a Vista de Propiedades
    Click Link    xpath=//a[contains(text(),'Vista de Propiedades')]
    Location Should Be    ${URL}vista_propiedades
    Title Should Be    Vista de Propiedades

Registrar Nueva Propiedad
    Click Button    xpath=//button[contains(text(),'Registrar Propiedad')]
    Input Text    id=direccion    ${DIRECCION}
    Input Text    id=comuna    ${COMUNA}
    Choose File   id=imagen    ${IMAGEN_PATH}
    Click Button    xpath=//button[contains(text(),'Registrar')]

Verificar Propiedad Registrada
    Wait Until Element Is Visible    xpath=//div[contains(@class, 'card') and contains(., '${DIRECCION}')]
    Element Should Be Visible    xpath=//div[contains(@class, 'card') and contains(., '${DIRECCION}')]

Cerrar Navegador
    Close Browser
