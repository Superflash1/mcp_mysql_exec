# Transports

> Learn about MCP's communication mechanisms

Transports in the Model Context Protocol (MCP) provide the foundation for communication between clients and servers. A transport handles the underlying mechanics of how messages are sent and received.

## Message Format

MCP uses [JSON-RPC](https://www.jsonrpc.org/) 2.0 as its wire format. The transport layer is responsible for converting MCP protocol messages into JSON-RPC format for transmission and converting received JSON-RPC messages back into MCP protocol messages.

There are three types of JSON-RPC messages used:

### Requests

```typescript
{
  jsonrpc: "2.0",
  id: number | string,
  method: string,
  params?: object
}
```

### Responses

```typescript
{
  jsonrpc: "2.0",
  id: number | string,
  result?: object,
  error?: {
    code: number,
    message: string,
    data?: unknown
  }
}
```

### Notifications

```typescript
{
  jsonrpc: "2.0",
  method: string,
  params?: object
}
```

## Built-in Transport Types

MCP currently defines two standard transport mechanisms:

### Standard Input/Output (stdio)

The stdio transport enables communication through standard input and output streams. This is particularly useful for local integrations and command-line tools.

Use stdio when:

* Building command-line tools
* Implementing local integrations
* Needing simple process communication
* Working with shell scripts

#### Server

<CodeGroup>
  ```typescript TypeScript
  const server = new Server(
    {
      name: "example-server",
      version: "1.0.0",
    },
    {
      capabilities: {},
    },
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);

```

  ```python Python
  app = Server("example-server")

  async with stdio_server() as streams:
      await app.run(
          streams[0],
          streams[1],
          app.create_initialization_options()
      )
```

</CodeGroup>

#### Client

<CodeGroup>
  ```typescript TypeScript
  const client = new Client(
    {
      name: "example-client",
      version: "1.0.0",
    },
    {
      capabilities: {},
    },
  );

  const transport = new StdioClientTransport({
    command: "./server",
    args: ["--option", "value"],
  });
  await client.connect(transport);

```

  ```python Python
  params = StdioServerParameters(
      command="./server",
      args=["--option", "value"]
  )

  async with stdio_client(params) as streams:
      async with ClientSession(streams[0], streams[1]) as session:
          await session.initialize()
```

</CodeGroup>

### Streamable HTTP

The Streamable HTTP transport uses HTTP POST requests for client-to-server communication and optional Server-Sent Events (SSE) streams for server-to-client communication.

Use Streamable HTTP when:

* Building web-based integrations
* Needing client-server communication over HTTP
* Requiring stateful sessions
* Supporting multiple concurrent clients
* Implementing resumable connections

#### How it Works

1. **Client-to-Server Communication**: Every JSON-RPC message from client to server is sent as a new HTTP POST request to the MCP endpoint
2. **Server Responses**: The server can respond either with:
   * A single JSON response (`Content-Type: application/json`)
   * An SSE stream (`Content-Type: text/event-stream`) for multiple messages
3. **Server-to-Client Communication**: Servers can send requests/notifications to clients via:
   * SSE streams initiated by client requests
   * SSE streams from HTTP GET requests to the MCP endpoint

#### Server

<CodeGroup>
  ```typescript TypeScript
  import express from "express";

  const app = express();

  const server = new Server(
    {
      name: "example-server",
      version: "1.0.0",
    },
    {
      capabilities: {},
    },
  );

  // MCP endpoint handles both POST and GET
  app.post("/mcp", async (req, res) => {
    // Handle JSON-RPC request
    const response = await server.handleRequest(req.body);

    // Return single response or SSE stream
    if (needsStreaming) {
      res.setHeader("Content-Type", "text/event-stream");
      // Send SSE events...
    } else {
      res.json(response);
    }
  });

  app.get("/mcp", (req, res) => {
    // Optional: Support server-initiated SSE streams
    res.setHeader("Content-Type", "text/event-stream");
    // Send server notifications/requests...
  });

  app.listen(3000);

```

  ```python Python
  from mcp.server.http import HttpServerTransport
  from starlette.applications import Starlette
  from starlette.routing import Route

  app = Server("example-server")

  async def handle_mcp(scope, receive, send):
      if scope["method"] == "POST":
          # Handle JSON-RPC request
          response = await app.handle_request(request_body)

          if needs_streaming:
              # Return SSE stream
              await send_sse_response(send, response)
          else:
              # Return JSON response
              await send_json_response(send, response)

      elif scope["method"] == "GET":
          # Optional: Support server-initiated SSE streams
          await send_sse_stream(send)

  starlette_app = Starlette(
      routes=[
          Route("/mcp", endpoint=handle_mcp, methods=["POST", "GET"]),
      ]
  )
```

</CodeGroup>

#### Client

<CodeGroup>
  ```typescript TypeScript
  const client = new Client(
    {
      name: "example-client",
      version: "1.0.0",
    },
    {
      capabilities: {},
    },
  );

  const transport = new HttpClientTransport(new URL("http://localhost:3000/mcp"));
  await client.connect(transport);

```

  ```python Python
  async with http_client("http://localhost:8000/mcp") as transport:
      async with ClientSession(transport[0], transport[1]) as session:
          await session.initialize()
```

</CodeGroup>

#### Session Management

Streamable HTTP supports stateful sessions to maintain context across multiple requests:

1. **Session Initialization**: Servers may assign a session ID during initialization by including it in an `Mcp-Session-Id` header
2. **Session Persistence**: Clients must include the session ID in all subsequent requests using the `Mcp-Session-Id` header
3. **Session Termination**: Sessions can be explicitly terminated by sending an HTTP DELETE request with the session ID

Example session flow:

```typescript
// Server assigns session ID during initialization
app.post("/mcp", (req, res) => {
  if (req.body.method === "initialize") {
    const sessionId = generateSecureId();
    res.setHeader("Mcp-Session-Id", sessionId);
    // Store session state...
  }
  // Handle request...
});

// Client includes session ID in subsequent requests
fetch("/mcp", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Mcp-Session-Id": sessionId,
  },
  body: JSON.stringify(request),
});
```

#### Resumability and Redelivery

To support resuming broken connections, Streamable HTTP provides:

1. **Event IDs**: Servers can attach unique IDs to SSE events for tracking
2. **Resume from Last Event**: Clients can resume by sending the `Last-Event-ID` header
3. **Message Replay**: Servers can replay missed messages from the disconnection point

This ensures reliable message delivery even with unstable network connections.

#### Security Considerations

When implementing Streamable HTTP transport, follow these security best practices:

1. **Validate Origin Headers**: Always validate the `Origin` header on all incoming connections to prevent DNS rebinding attacks
2. **Bind to Localhost**: When running locally, bind only to localhost (127.0.0.1) rather than all network interfaces (0.0.0.0)
3. **Implement Authentication**: Use proper authentication for all connections
4. **Use HTTPS**: Always use TLS/HTTPS for production deployments
5. **Validate Session IDs**: Ensure session IDs are cryptographically secure and properly validated

Without these protections, attackers could use DNS rebinding to interact with local MCP servers from remote websites.

### Server-Sent Events (SSE) - Deprecated

<Note>
  SSE as a standalone transport is deprecated as of protocol version 2024-11-05.
  It has been replaced by Streamable HTTP, which incorporates SSE as an optional
  streaming mechanism. For backwards compatibility information, see the
  [backwards compatibility](#backwards-compatibility) section below.
</Note>

The legacy SSE transport enabled server-to-client streaming with HTTP POST requests for client-to-server communication.

Previously used when:

* Only server-to-client streaming is needed
* Working with restricted networks
* Implementing simple updates

#### Legacy Security Considerations

The deprecated SSE transport had similar security considerations to Streamable HTTP, particularly regarding DNS rebinding attacks. These same protections should be applied when using SSE streams within the Streamable HTTP transport.

#### Server

<CodeGroup>
  ```typescript TypeScript
  import express from "express";

  const app = express();

  const server = new Server(
    {
      name: "example-server",
      version: "1.0.0",
    },
    {
      capabilities: {},
    },
  );

  let transport: SSEServerTransport | null = null;

  app.get("/sse", (req, res) => {
    transport = new SSEServerTransport("/messages", res);
    server.connect(transport);
  });

  app.post("/messages", (req, res) => {
    if (transport) {
      transport.handlePostMessage(req, res);
    }
  });

  app.listen(3000);

```

  ```python Python
  from mcp.server.sse import SseServerTransport
  from starlette.applications import Starlette
  from starlette.routing import Route

  app = Server("example-server")
  sse = SseServerTransport("/messages")

  async def handle_sse(scope, receive, send):
      async with sse.connect_sse(scope, receive, send) as streams:
          await app.run(streams[0], streams[1], app.create_initialization_options())

  async def handle_messages(scope, receive, send):
      await sse.handle_post_message(scope, receive, send)

  starlette_app = Starlette(
      routes=[
          Route("/sse", endpoint=handle_sse),
          Route("/messages", endpoint=handle_messages, methods=["POST"]),
      ]
  )
```

</CodeGroup>

#### Client

<CodeGroup>
  ```typescript TypeScript
  const client = new Client(
    {
      name: "example-client",
      version: "1.0.0",
    },
    {
      capabilities: {},
    },
  );

  const transport = new SSEClientTransport(new URL("http://localhost:3000/sse"));
  await client.connect(transport);

```

  ```python Python
  async with sse_client("http://localhost:8000/sse") as streams:
      async with ClientSession(streams[0], streams[1]) as session:
          await session.initialize()
```

</CodeGroup>

## Custom Transports

MCP makes it easy to implement custom transports for specific needs. Any transport implementation just needs to conform to the Transport interface:

You can implement custom transports for:

* Custom network protocols
* Specialized communication channels
* Integration with existing systems
* Performance optimization

<CodeGroup>
  ```typescript TypeScript
  interface Transport {
    // Start processing messages
    start(): Promise<void>;

    // Send a JSON-RPC message
    send(message: JSONRPCMessage): Promise`<void>`;

    // Close the connection
    close(): Promise`<void>`;

    // Callbacks
    onclose?: () => void;
    onerror?: (error: Error) => void;
    onmessage?: (message: JSONRPCMessage) => void;
  }

```

  ```python Python
  # Note that while MCP Servers are often implemented with asyncio, we recommend
  # implementing low-level interfaces like transports with `anyio` for wider compatibility.

  @contextmanager
  async def create_transport(
      read_stream: MemoryObjectReceiveStream[JSONRPCMessage | Exception],
      write_stream: MemoryObjectSendStream[JSONRPCMessage]
  ):
      """
      Transport interface for MCP.

      Args:
          read_stream: Stream to read incoming messages from
          write_stream: Stream to write outgoing messages to
      """
      async with anyio.create_task_group() as tg:
          try:
              # Start processing messages
              tg.start_soon(lambda: process_messages(read_stream))

              # Send messages
              async with write_stream:
                  yield write_stream

          except Exception as exc:
              # Handle errors
              raise exc
          finally:
              # Clean up
              tg.cancel_scope.cancel()
              await write_stream.aclose()
              await read_stream.aclose()
```

</CodeGroup>

## Error Handling

Transport implementations should handle various error scenarios:

1. Connection errors
2. Message parsing errors
3. Protocol errors
4. Network timeouts
5. Resource cleanup

Example error handling:

<CodeGroup>
  ```typescript TypeScript
  class ExampleTransport implements Transport {
    async start() {
      try {
        // Connection logic
      } catch (error) {
        this.onerror?.(new Error(`Failed to connect: ${error}`));
        throw error;
      }
    }

    async send(message: JSONRPCMessage) {
      try {
        // Sending logic
      } catch (error) {
        this.onerror?.(new Error(`Failed to send message: ${error}`));
        throw error;
      }
    }
  }

```

  ```python Python
  # Note that while MCP Servers are often implemented with asyncio, we recommend
  # implementing low-level interfaces like transports with `anyio` for wider compatibility.

  @contextmanager
  async def example_transport(scope: Scope, receive: Receive, send: Send):
      try:
          # Create streams for bidirectional communication
          read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
          write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

          async def message_handler():
              try:
                  async with read_stream_writer:
                      # Message handling logic
                      pass
              except Exception as exc:
                  logger.error(f"Failed to handle message: {exc}")
                  raise exc

          async with anyio.create_task_group() as tg:
              tg.start_soon(message_handler)
              try:
                  # Yield streams for communication
                  yield read_stream, write_stream
              except Exception as exc:
                  logger.error(f"Transport error: {exc}")
                  raise exc
              finally:
                  tg.cancel_scope.cancel()
                  await write_stream.aclose()
                  await read_stream.aclose()
      except Exception as exc:
          logger.error(f"Failed to initialize transport: {exc}")
          raise exc
```

</CodeGroup>

## Best Practices

When implementing or using MCP transport:

1. Handle connection lifecycle properly
2. Implement proper error handling
3. Clean up resources on connection close
4. Use appropriate timeouts
5. Validate messages before sending
6. Log transport events for debugging
7. Implement reconnection logic when appropriate
8. Handle backpressure in message queues
9. Monitor connection health
10. Implement proper security measures

## Security Considerations

When implementing transport:

### Authentication and Authorization

* Implement proper authentication mechanisms
* Validate client credentials
* Use secure token handling
* Implement authorization checks

### Data Security

* Use TLS for network transport
* Encrypt sensitive data
* Validate message integrity
* Implement message size limits
* Sanitize input data

### Network Security

* Implement rate limiting
* Use appropriate timeouts
* Handle denial of service scenarios
* Monitor for unusual patterns
* Implement proper firewall rules
* For HTTP-based transports (including Streamable HTTP), validate Origin headers to prevent DNS rebinding attacks
* For local servers, bind only to localhost (127.0.0.1) instead of all interfaces (0.0.0.0)

## Debugging Transport

Tips for debugging transport issues:

1. Enable debug logging
2. Monitor message flow
3. Check connection states
4. Validate message formats
5. Test error scenarios
6. Use network analysis tools
7. Implement health checks
8. Monitor resource usage
9. Test edge cases
10. Use proper error tracking

## Backwards Compatibility

To maintain compatibility between different protocol versions:

### For Servers Supporting Older Clients

Servers wanting to support clients using the deprecated HTTP+SSE transport should:

1. Host both the old SSE and POST endpoints alongside the new MCP endpoint
2. Handle initialization requests on both endpoints
3. Maintain separate handling logic for each transport type

### For Clients Supporting Older Servers

Clients wanting to support servers using the deprecated transport should:

1. Accept server URLs that may use either transport
2. Attempt to POST an `InitializeRequest` with proper `Accept` headers:
   * If successful, use Streamable HTTP transport
   * If it fails with 4xx status, fall back to legacy SSE transport
3. Issue a GET request expecting an SSE stream with `endpoint` event for legacy servers

Example compatibility detection:

```typescript
async function detectTransport(serverUrl: string): Promise<TransportType> {
  try {
    // Try Streamable HTTP first
    const response = await fetch(serverUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "initialize",
        params: {
          /* ... */
        },
      }),
    });

    if (response.ok) {
      return "streamable-http";
    }
  } catch (error) {
    // Fall back to legacy SSE
    const sseResponse = await fetch(serverUrl, {
      method: "GET",
      headers: { Accept: "text/event-stream" },
    });

    if (sseResponse.ok) {
      return "legacy-sse";
    }
  }

  throw new Error("Unsupported transport");
}
```
