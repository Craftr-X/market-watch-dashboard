# Terminal UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the dashboard frontend into a dark financial-terminal interface with stronger market telemetry, clearer risk display, and improved table readability.

**Architecture:** Keep the existing single Next.js client page and API contracts. Refactor only the presentation layer in `frontend/app/page.tsx` and `frontend/app/styles.css`, adding small helper functions for computed metrics and semantic status labels.

**Tech Stack:** Next.js App Router, React, TypeScript, CSS, lucide-react.

---

### Task 1: Restructure Dashboard Markup

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] Add computed metrics for average index change, strongest sectors, and risk count.
- [ ] Replace the plain topbar with a terminal masthead containing title, status metadata, and refresh action.
- [ ] Replace the overview block with a command strip and index ticker cards.
- [ ] Preserve existing API calls and table data mappings.

### Task 2: Apply Terminal Visual System

**Files:**
- Modify: `frontend/app/styles.css`

- [ ] Replace the light palette with deep graphite background, cyan/amber accents, red-up/green-down market colors.
- [ ] Add terminal panel, badge, table, and responsive styles.
- [ ] Ensure table text remains readable and horizontally scrollable on mobile.
- [ ] Keep risk disclaimer visually prominent.

### Task 3: Verify Build and Launch

**Files:**
- No code changes expected.

- [ ] Run `npm run build` in `frontend`.
- [ ] Confirm backend is listening on `127.0.0.1:8000`; start it if needed.
- [ ] Start frontend with `npm run dev`.
- [ ] Report the local frontend URL and backend URL.

## Self-Review

The plan covers the approved financial-terminal direction, keeps scope limited to frontend UI, preserves API contracts, and includes verification. No placeholders or unresolved decisions remain.
