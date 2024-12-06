*** Settings ***
Documentation     Pruebas para la página de empresas: verificar visualización y acciones
Library           SeleniumLibrary

*** Variables ***
${BROWSER}        Chrome
${URL}            http://127.0.0.1:5000/login
${EMPRESAS_URL}   http://127.0.0.1:5000/empresas
${USUARIO}        agustinikus
${CONTRASENA}     amparo12
${EMPRESA}        Empresa Ejemplo
${CODIGO_EMPRESA}   6TVI1DiWkIdZ6dRLUnGy

*** Test Cases ***
Prueba de Carga de Página
    [Documentation]    Verifica que la página cargue correctamente y que el título sea "Empresas"
    Abrir Página de Empresas
    Verificar Carga de Página
    Cerrar Navegador

Prueba de Visualización de Tabla de Empresas
    [Documentation]    Verifica que la tabla de empresas sea visible y tenga al menos una fila
    Abrir Página de Empresas
    Verificar Tabla de Empresas Visible
    Verificar Empresa en la Tabla
    Cerrar Navegador

Prueba de Crear Nueva Empresa
    [Documentation]    Prueba que se puede abrir el modal y crear una nueva empresa
    Abrir Página de Empresas
    Abrir Modal Crear Empresa
    Rellenar Formulario Crear Empresa
    Enviar Formulario Crear Empresa
    Verificar Empresa Creada en la Tabla
    Cerrar Navegador

Prueba de Añadir Empresa con Código
    [Documentation]    Prueba que se puede abrir el modal y añadir una empresa con un código
    Abrir Página de Empresas
    Abrir Modal Añadir Empresa
    Rellenar Formulario Añadir Empresa
    Enviar Formulario Añadir Empresa
    Verificar Empresa Añadida en la Tabla
    Cerrar Navegador

*** Keywords ***
Abrir Página de Empresas
    Open Browser    ${URL}    ${BROWSER}
    Maximize Browser Window
    Iniciar Sesion
    Go To    ${EMPRESAS_URL}
    Location Should Be    ${EMPRESAS_URL}

Iniciar Sesion
    [Arguments]    ${usuario}=${USUARIO}    ${contrasena}=${CONTRASENA}
    Input Text    id=username    ${usuario}
    Input Text    id=password    ${contrasena}
    Click Button    xpath=//button[@type='submit']
    Wait Until Page Contains    Empresas

Verificar Carga de Página
    Title Should Be    Empresas

Verificar Tabla de Empresas Visible
    Wait Until Element Is Visible    xpath=//table[@class='table']
    Element Should Be Visible    xpath=//table[@class='table']

Verificar Empresa en la Tabla
    # Verifica que haya al menos una fila en la tabla (excluyendo la cabecera)
    Element Should Be Visible    xpath=//table[@class='table']/tbody/tr

Abrir Modal Crear Empresa
    Click Button    xpath=//button[contains(text(), 'Crear Empresa')]
    Wait Until Element Is Visible    id=formModal
    Element Should Be Visible    id=formModal

Rellenar Formulario Crear Empresa
    Input Text    id=nombre    ${EMPRESA}

Enviar Formulario Crear Empresa
    Click Button    xpath=//button[contains(text(), 'Crear')]

Verificar Empresa Creada en la Tabla
    Wait Until Element Is Visible    xpath=//table[@class='table']/tbody/tr[td[contains(text(), '${EMPRESA}')]]
    Element Should Be Visible    xpath=//table[@class='table']/tbody/tr[td[contains(text(), '${EMPRESA}')]]

Abrir Modal Añadir Empresa
    Click Button    xpath=//button[contains(text(), 'Añadir Empresa')]
    Wait Until Element Is Visible    id=formModal2
    Element Should Be Visible    id=formModal2

Rellenar Formulario Añadir Empresa
    Input Text    id=codigo    ${CODIGO_EMPRESA}

Enviar Formulario Añadir Empresa
    Click Button    xpath=//button[contains(text(), 'Añadir Empresa')]

Verificar Empresa Añadida en la Tabla
    Wait Until Element Is Visible    xpath=//table[@class='table']/tbody/tr[td[contains(text(), '${CODIGO_EMPRESA}')]]
    Element Should Be Visible    xpath=//table[@class='table']/tbody/tr[td[contains(text(), '${CODIGO_EMPRESA}')]]

Cerrar Navegador
    Close Browser
