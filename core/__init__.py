"""Shared plumbing every module may use: paths, config, logging, http, errors.

Not a framework and not a base class for ingestors. These are ordinary
functions that happen to be needed by more than one caller — the one place
paths are worked out, the one place the .env file is read, the one place an
API key can be printed by accident, the one place an HTTP timeout is set.
See CLAUDE.md ("shared FUNCTIONS yes, shared SHAPE no") and ARCHITECTURE.md §2.
"""
