*** Settings ***
Documentation     Pruebas de navegación y funcionalidades del menú en la aplicación web.
Library           SeleniumLibrary
Suite Setup       Open Browser With Options
Suite Teardown    Close Browser
Test Setup        Maximize Browser Window

*** Variables ***
${URL}            http://127.0.0.1:5000/menu
${BROWSER}        chrome

*** Test Cases ***
Test Sidebar Navigation
    [Documentation]    Verifica la navegación en la barra lateral
    Wait Until Page Contains Element    xpath=//ul[@class='sidebar-menu']    timeout=15
    ${dashboard_button}=    Get WebElement    xpath=//a[span/text()='Dashboard']
    Click Element    ${dashboard_button}
    Wait Until Page Contains Element    id=dynamic-content    timeout=10

Test Header Navigation
    [Documentation]    Verifica los elementos de navegación del encabezado
    Wait Until Page Contains Element    css=.navbar    timeout=15
    ${search_bar}=    Get WebElement    css=input.form-control
    Input Text    ${search_bar}    prueba de búsqueda
    Click Element    css=.icon-magnifier
    Wait Until Page Contains Element    css=.navbar-nav    timeout=10

Test User Dropdown
    [Documentation]    Verifica la funcionalidad del menú desplegable de usuario
    Wait Until Page Contains Element    css=.user-profile    timeout=15
    Click Element    css=.user-profile
    Wait Until Page Contains Element    css=.dropdown-menu    timeout=10
    ${account_option}=    Get WebElement    css=.dropdown-item i.icon-wallet
    Click Element    ${account_option}
    Wait Until Page Contains Element    text=Account    timeout=10

*** Keywords ***
Open Browser With Options
    [Arguments]    ${url}
    ${chrome options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    Call Method    ${chrome options}    add_argument    --no-sandbox
    Create Webdriver    Chrome    chrome_options=${chrome options}
    Go To    ${url}
