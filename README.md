# Neyra VPN

Autonomous Telegram bot + GitHub Pages subscription engine for Neyra VPN.

## Tiers

- **Neyra Basic** — all structurally valid collected nodes.
- **Neyra Best** — a smaller ranked pool using a deterministic quality heuristic.
- **Neyra Creator** — creator-only ranked pool with a larger limit.

The ranking is **not** a guarantee of reachability or speed. It scores configuration characteristics; public nodes can disappear or be blocked at any time.

## Happ auto-update

Neyra subscriptions include Happ application-management directives in the subscription body:

- `#profile-update-interval: 4`
- `#subscription-auto-update-enable: 1`
- `#subscription-auto-update-open-enable: 1`
- `#subscription-ping-onopen-enabled: 1`

Happ documents these parameters and supports subscription auto-update in hours, including delivery via the subscription body.

## Runtime secrets (Railway)

Required:

- `BOT_TOKEN`
- `ADMIN_USER_ID`

Optional:

- `NEYRA_BASE_URL`
- `BEST_SUBSCRIPTION_URL`
- `CREATOR_SUBSCRIPTION_URL`
- `LOG_LEVEL`
- `ACCESS_FILE`

## Access requests

Users can request access to Neyra Best from the bot. The creator receives an approval/deny button. The runtime registry is stored in `ACCESS_FILE`; on a platform without persistent storage, approvals may reset after a redeploy. For persistent approvals, mount a small Railway Volume or manage an allow-list through environment variables in a future iteration.

## GitHub Pages

The scheduled workflow rebuilds every four hours and publishes the generated `docs/` directory without committing generated files back to the repository.
