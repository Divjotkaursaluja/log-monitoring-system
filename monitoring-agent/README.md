# AI Log Monitoring Agent

This agent is installed on a client machine and forwards application logs to the FastAPI backend.

## Flow

```text
Client app.log files
-> monitoring agent
-> /register-agent
-> secure token stored in agent_state.json
-> /logs with Bearer token
-> MySQL
-> dashboard
```

## Development

```bat
install_agent.bat
start_agent.bat
```

## Build EXE

```bat
build_agent.bat
```

Output:

```text
dist/agent.exe
dist/config.yaml
```

Edit `dist/config.yaml` on each client machine before installing the service.

## Install As Windows Service

Run Command Prompt as Administrator:

```bat
install_service.bat
```

Remove service:

```bat
uninstall_service.bat
```

## Runtime Files

- `agent_state.json`: agent id and secure token returned by backend.
- `buffered_logs.jsonl`: failed log sends stored locally for retry.

Do not share `agent_state.json`; it contains the agent token.
