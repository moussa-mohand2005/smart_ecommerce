# Smart Shoe Next.js Dashboard

Production-oriented replacement for `step4_bi_dashboard.py`. It keeps the existing MySQL database and Python data/ML pipeline, while moving presentation and read-only APIs to Next.js.

## Run locally

The app automatically reads `../.env` when launched from this directory. You can instead copy `.env.example` to `.env.local` and set the database and Groq values there.

```bash
npm install
npm run dev
```

Open <http://localhost:3000>.

## Production

```bash
npm run typecheck
npm run build
npm start
```

Or build the included Dockerfile from this directory.

## Feature parity

- Global brand, price, score, and text filters
- Six live KPIs
- Ranked product cards
- Price/score and price-band market charts
- Cluster composition and PCA style map
- LLM-generated customer personas
- Brand ranking, positioning, and association rules
- Paginated product explorer
- Server-side Groq strategic report
- Validated, parameterized MCP-style tool console

Database and API secrets are read only on the server. Product queries use placeholders, pagination is server-side, and external catalog text is rendered as React text rather than injected HTML.
