# Alerting Limitations

VAS sends violence alerts via Telegram. For a local single-camera demo
that's fine. For anything beyond that, it has real gaps.

## What Telegram gives you

No infrastructure to set up. One bot token, one chat ID, and alerts with
snapshots arrive in under two seconds. That's the whole appeal.

## Where it breaks down

**No delivery guarantee.** The alert is an HTTP call to Telegram's servers.
If the network drops after three retries, the alert is gone. No dead-letter
queue, no retry persistence, no way to know it failed unless you watch the
logs.

**No acknowledgement loop.** There's no way to know if a human saw the alert
and acted on it. An alert sent to an unmonitored chat is the same as no alert.

**Single destination.** One chat, no routing by severity, no on-call schedule,
no escalation if nobody responds in five minutes.

**Rate limits.** Telegram allows roughly 1 message per second to the same
chat. A multi-camera setup hitting that ceiling drops alerts silently.

**No tamper-evident channel log.** VAS records every Telegram call in the
audit log. But if the chat history is cleared or Telegram removes the
message, the delivery record on the channel side is gone.

## What production would need

SMS via Twilio adds delivery receipts. Email adds a tracked open. PagerDuty
or OpsGenie adds on-call routing and acknowledgement. A SIEM like Splunk or
Elastic correlates violence alerts with other security events and keeps a
log you can actually trust in court.

## Why Telegram anyway

This project runs locally, one camera, one operator. Telegram gets a
snapshot into your hands in two seconds with no infrastructure overhead.
Running PagerDuty for a local demo would be like bolting a jet engine onto
a bicycle. The limitations above are deliberate tradeoffs, not oversights.