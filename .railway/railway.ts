import {
  defineRailway,
  github,
  postgres,
  preserve,
  project,
  service,
} from "railway/iac";

export default defineRailway((ctx) => {
  const isProduction = ctx.environment === "prod";
  const database = postgres("Postgres");

  const web = service("web", {
    source: github("mxagar/notes_webapp", { branch: "main" }),
    healthcheck: "/health/",
    healthcheckTimeout: 120,
    preDeploy: "/app/.venv/bin/python src/manage.py migrate --noinput",
    env: {
      DATABASE_URL: database.env.DATABASE_URL,
      DJANGO_DEBUG: "false",
      DJANGO_SECRET_KEY: preserve(),
      DJANGO_SECURE_SSL_REDIRECT: "true",
      DJANGO_SECURE_HSTS_SECONDS: isProduction ? "31536000" : "0",
      RUN_MIGRATIONS_ON_STARTUP: "false",
    },
  });

  return project("notes-app", {
    resources: [database, web],
  });
});
