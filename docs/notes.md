# 🧠 Development Notes

## Key Decisions

- Use cooldown instead of blocking strategies
- Use trade deduplication instead of strategy blocking
- Multi-timeframe logic:
  - 1m → entry
  - 5m → structure
  - 15m → bias

## Known Issues

- Telegram may silently fail → needs retry system
- Confidence inconsistency across strategies

## Future Ideas

- Listing Engine
- Smart Market Scanner
- Strategy auto-ranking