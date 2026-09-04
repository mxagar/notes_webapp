# Railway Infrastructure

`railway.ts` is the source-controlled Railway project definition. The same
file is planned and applied separately against the `dev` and `prod`
environments.

Install the pinned DSL package before evaluating the configuration:

```bash
npm ci
```

Always inspect `railway config plan` before `railway config apply`. Keep
secrets in Railway variables rather than this directory.
