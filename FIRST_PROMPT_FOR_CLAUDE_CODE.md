# Do this

1. Put `controlroom-for-claude-code.zip` in an empty folder.
2. Open Claude Code in that folder.
3. Paste the message below. That's it.

# Paste this into Claude Code

There is a zip file in this folder called controlroom-for-claude-code.zip.
Set up the project from it:

1. Unzip it here so that CLAUDE.md is at the top level of this folder, then
   delete the zip.
2. git init, add everything, commit as "v0 docs".
3. Check whether uv and Python 3.12 are installed. If not, tell me the exact
   install command for my OS and stop until I confirm.
4. Run uv init and add: duckdb pandas httpx streamlit pytest python-dotenv.
5. Copy .env.example to .env. Then tell me the two URLs where I get free API
   keys and stop until I paste the keys into .env myself.
6. Create data/bronze/ and confirm data/ is in .gitignore.
7. Commit as "environment".

Then read CLAUDE.md, docs/SCOPE.md, docs/DESIGN.md and docs/PLAN.md. Tell me
in plain language what the four unbreakable rules are and what you are
forbidden from building, so I know you've understood.

Then do the Week 1 CC tasks in docs/PLAN.md: db/schema.sql, db/init.py,
db/seed_entities.sql, db/make_split.py. Stop after those. I am writing
ingest/fred.py myself and will show you when it's ready.

I have not written much Python before. Explain what each file does in one
plain sentence when you create it. Delete FIRST_PROMPT_FOR_CLAUDE_CODE.md
when setup is done.
