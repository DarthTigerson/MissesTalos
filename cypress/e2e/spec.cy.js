describe('Manage admins', () => {
  it('adds admin', function () {
    cy.login("hermes", "hermes")
    cy.visit("http://0.0.0.0:8000/")

    cy.get('#navbarDropdownMenuLink').click()
    cy.get('[href="/admin"]').click()
    cy.url().should("include", "/admin/");

    cy.get('.col-md-8 > .card > .card-header > .btn').click()
    cy.url().should("include", "/admin/add_user");


    cy.get('.card-body > :nth-child(1) > .form-control').type("edson")
    cy.get(':nth-child(1) > .card-body > :nth-child(2) > .form-control').type("Edson Manuel")
    cy.get(':nth-child(3) > .form-control').type("Carballo Vera")
    cy.get(':nth-child(4) > .form-control').select("Admin")
    cy.get(':nth-child(3) > .card-body > .form-group > .form-control').type("contrasena")
    cy.get('[type="submit"]').click()
    cy.url().should("contain", "/admin/");
  });

  it("removes admin", () => {
    cy.login("hermes", "hermes")
    cy.visit("http://0.0.0.0:8000/")

    cy.get('#navbarDropdownMenuLink').click()
    cy.get('[href="/admin"]').click()
    cy.url().should("include", "/admin/");

    cy.get(':nth-child(1) > :nth-child(6) > .btn').click()
    cy.get('.btn-danger').click()
    cy.url().should("include", "/admin/");
  });
});