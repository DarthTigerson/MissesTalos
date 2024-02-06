// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add("login", (username, password) => {
  cy.session(username, () => {
    cy.visit("http://0.0.0.0:8000/admin/login")
    cy.get('form > :nth-child(1) > .form-control').type(username)
    cy.get(':nth-child(2) > .form-control').type(password)
    cy.get('.btn').click();
    cy.url().should("include", "/");
  }, {
    validate: () => {
      cy.getCookie("access_token").should("exist")
    }
  });
});