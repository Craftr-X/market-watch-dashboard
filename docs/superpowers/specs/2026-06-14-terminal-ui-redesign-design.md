# Terminal UI Redesign Design

## Goal

Redesign the A-share dashboard into a technology-forward financial terminal while preserving the current product boundary: market learning, daily review, strong-stock observation, and visible risk reminders.

## Selected Direction

The user selected Direction A: Financial Terminal. The interface should use a dark terminal style, dense but readable data tables, red-up/green-down market coloring, and crisp operational controls. It may borrow restrained details from the command-center concept, such as a stronger status header, luminous borders, and compact market telemetry.

## Layout

The dashboard remains a single-page daily workflow:

1. Header with product name, update time, data source, and refresh button.
2. Risk disclaimer banner that stays visually prominent.
3. Market command strip with market state, average index change, strong direction count, risk count, and index cards.
4. Two-column section for sector heat and risk radar.
5. Full-width strong observation table with score badges, reasons, and risk notes.
6. Daily report panel with summary and risk tags.

## Visual System

Use a deep graphite/ink background instead of a plain light page. Accent colors are cyan for system/UI affordances, amber for warnings, red for rising A-share values, and green for falling values. Borders, subtle scan-line/grid backgrounds, and compact badges create the technology feel without hiding the data.

## UX Requirements

- Risk disclaimer remains above the data and easy to notice.
- Strong observation remains table-first for scanning.
- Refresh button shows a loading state.
- Empty/loading states do not cause large layout jumps.
- Mobile keeps the key summary readable and allows horizontal table scrolling.
- No wording implies buy/sell advice, target prices, or guaranteed returns.

## Verification

- Run the Next.js production build after changes.
- Start the frontend dev server and confirm the local URL.
- Confirm the backend API is still reachable from the page.
