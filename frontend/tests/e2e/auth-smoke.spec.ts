import { expect, test } from "@playwright/test";

test("muestra login accesible y conserva tema", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Bienvenido de vuelta" })).toBeVisible();
  await expect(page.getByLabel("Correo")).toBeVisible();
  await expect(page.getByLabel("Contraseña")).toBeVisible();
  await expect(page.getByRole("button", { name: /ingresar/i })).toBeVisible();
});

test("protege las rutas internas sin sesión", async ({ page }) => {
  await page.route("**/api/v1/auth/session/", route =>
    route.fulfill({ status: 200, contentType: "application/json", body: '{"authenticated":false}' }),
  );
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/);
});
