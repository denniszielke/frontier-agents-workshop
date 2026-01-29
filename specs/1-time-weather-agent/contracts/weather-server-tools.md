# MCP Tool Contracts: Weather Server (04-weather-server)

**Server Name**: WeatherTimeSpace  
**Endpoint**: `http://localhost:8001/mcp`  
**Transport**: Streamable HTTP

## Tools

### list_supported_locations

Returns the list of cities supported by this weather server.

**Parameters**: None

**Returns**: `list[string]` - Array of supported city names

**Example Response**:
```json
["Seattle", "New York", "London", "Berlin", "Tokyo", "Sydney"]
```

---

### get_weather_at_location

Returns a weather description for a supported location based on the current local time there.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| location | string | Yes | City name (case-insensitive) |

**Returns**: `string` - Weather description with local time and time-of-day bucket

**Time-of-Day Buckets**:
| Bucket | Hours (Local) | Description |
|--------|---------------|-------------|
| morning | 05:00 - 11:59 | Cool and clear with a light breeze |
| afternoon | 12:00 - 17:59 | Mild temperatures with scattered clouds and good visibility |
| evening | 18:00 - 21:59 | Calm conditions with a gentle breeze and fading light |
| night | 22:00 - 04:59 | Quiet, mostly clear skies and cooler air |

**Example Request**:
```json
{
  "location": "London"
}
```

**Example Response** (varies by time of day):
```json
"Weather for London at 2026-01-29 14:30 (afternoon): Mild temperatures with scattered clouds and good visibility."
```

**Error Response** (unsupported location):
```json
"Unsupported location. Use `list_supported_locations` to see valid options."
```

---

### get_weather_for_multiple_locations

Returns weather descriptions for multiple locations at once.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| locations | list[string] | Yes | Array of city names |

**Returns**: `list[string]` - Array of weather descriptions (same format as `get_weather_at_location`)

**Example Request**:
```json
{
  "locations": ["London", "Berlin", "Tokyo"]
}
```

**Example Response**:
```json
[
  "Weather for London at 2026-01-29 14:30 (afternoon): Mild temperatures with scattered clouds and good visibility.",
  "Weather for Berlin at 2026-01-29 15:30 (afternoon): Mild temperatures with scattered clouds and good visibility.",
  "Weather for Tokyo at 2026-01-29 23:30 (night): Quiet, mostly clear skies and cooler air."
]
```

---

## Resources

### config://version

Returns server version information.

**Response**:
```json
{
  "version": "1.0.0",
  "features": ["tools", "resources"]
}
```

---

## Prompts

### describe_weather_capabilities

Generates a prompt explaining how to use this MCP server.

**Parameters**: None

**Returns**: List of prompt messages describing:
1. How to list supported locations
2. How to get weather for a single location
3. How to fetch weather for multiple locations

---

## Location Support Matrix

| Location | Timezone | Supported |
|----------|----------|-----------|
| Seattle | America/Los_Angeles | ✅ |
| New York | America/New_York | ✅ |
| London | Europe/London | ✅ |
| Berlin | Europe/Berlin | ✅ |
| Tokyo | Asia/Tokyo | ✅ |
| Sydney | Australia/Sydney | ✅ |
| Paris | - | ❌ |
| Amsterdam | - | ❌ |

**Note**: For locations not in this list, the server returns an error message suggesting the user call `list_supported_locations`.
