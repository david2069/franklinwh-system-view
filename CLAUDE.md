# franklinwh-system-view

Shared by the FranklinWH Direct Connect bridge and the Modbus bridge. Design: direct-connect-bridge #428 (approved 2026-11-01).

- No FranklinWH device code here. Bridges build the payload from their own readings; anything they can't read is left out or listed in `unavailable`. Nothing is guessed in this package.
- Anything uncertain is a user setting in the bridge, not a guess here.
- Layout lives in Python (`layout.py`) and is tested there; the page only draws it. Keep the page dependency-free.
- Design for the common site first: US split-phase, one aGate, one or two aPowers, often no solar.
- Branch and PR for every change; never commit to main. Every change has a test that fails without it.
- Public repo: no serials, IPs, emails, hostnames or tokens in code, tests, docs or commits.
