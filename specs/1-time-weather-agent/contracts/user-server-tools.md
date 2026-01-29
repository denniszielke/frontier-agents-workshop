# MCP Tool Contracts: User Server (02-user-server)

**Server Name**: UserTimeLocation  
**Endpoint**: `http://localhost:8002/mcp`  
**Transport**: Streamable HTTP

## Tools

### get_current_user

Returns the username of the current logged-in user.

**Parameters**: None

**Returns**: `string` - The username

**Example Response**:
```json
"Dennis"
```

---

### get_current_location

Returns the timezone location for a given username.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | The username to look up |

**Returns**: `string` - IANA timezone identifier (e.g., "Europe/Berlin")

**Example Request**:
```json
{
  "username": "Dennis"
}
```

**Example Response**:
```json
"Europe/Berlin"
```

**Default Behavior**: Returns "Europe/London" for unknown usernames

---

### get_current_time

Returns the current time for a given timezone location.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| location | string | Yes | IANA timezone (e.g., "Europe/London", "America/New_York") |

**Returns**: `string` - Formatted time string (12-hour format with AM/PM)

**Example Request**:
```json
{
  "location": "Europe/London"
}
```

**Example Response**:
```json
"02:30:45 PM"
```

**Error Response**:
```json
"Sorry, I couldn't find the timezone for that location."
```

**Timezone Mapping Reference** (for agent instructions):
| City | Timezone |
|------|----------|
| London | Europe/London |
| Berlin | Europe/Berlin |
| New York | America/New_York |
| Seattle | America/Los_Angeles |
| Tokyo | Asia/Tokyo |
| Sydney | Australia/Sydney |

---

### move

Updates a user's location to a new timezone.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | The username to update |
| newlocation | string | Yes | New IANA timezone identifier |

**Returns**: `boolean` - True if successful, False if user not found

**Example Request**:
```json
{
  "username": "Dennis",
  "newlocation": "Europe/London"
}
```

**Example Response**:
```json
true
```

---

## Resources

### config://version

Returns server version information.

**Response**:
```json
{
  "version": "1.2.0",
  "features": ["tools", "resources"]
}
```

---

## Prompts

### get_user_time

Generates a prompt to find the current time for a user.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | The username to look up |

**Returns**: List of prompt messages for time lookup workflow
