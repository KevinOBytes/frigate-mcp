---
name: AGENTS.md
description: Describe what this custom agent does and when to use it.
argument-hint: The inputs this agent expects, e.g., "a task to implement" or "a question to answer".
tools: ['frigate', 'http', 'mqtt', 'json', 'camera', 'workflow', 'logging', 'alerts', 'notifications', 'commands', 'tools', 'search']
---

# Frigate-MCP Agent

The Frigate-MCP agent, in this repo, is responsible for managing and interacting with multiple cameras within the Frigate ecosystem. It provides a structured way to control camera settings, capture images and video clips, and handle multi-camera configurations efficiently.

It runs via Docker containers, allowing it to easily integrate with the Frigate ecosystem and manage multiple cameras efficiently.

It provides a consistent interface for interacting with cameras, ensuring that all camera operations are executed reliably and efficiently.

It abstracts the complexities of multi-camera management, providing users with a simplified and unified interface for all camera-related operations.

It uses the Model Context Protocol (MCP) to communicate with the Frigate ecosystem, ensuring efficient and reliable multi-camera management.

It uses the Frigate Python library to interact with the Frigate ecosystem, enabling seamless control and management of multiple cameras.

It ensures that all camera operations are executed in a consistent and reliable manner, providing users with confidence in the management of their multi-camera setups.

It provides detailed feedback and status information for all camera operations, allowing users to monitor and verify the results of their actions.

It supports extensibility, allowing developers to add new features and capabilities to the agents as the Frigate ecosystem evolves.

It uses json to structure and communicate data between the agents and the Frigate ecosystem, ensuring consistent and reliable information exchange.

It provides robust error handling and recovery mechanisms, ensuring that the agents can gracefully handle failures and maintain reliable operation within the Frigate ecosystem.

It provides comprehensive logging and monitoring capabilities, allowing users to track the performance and behavior of the agents within the Frigate ecosystem.

It provides secure communication mechanisms, ensuring that all interactions between the agents and the Frigate ecosystem are protected against unauthorized access and tampering.

It supports real-time notifications and alerts, allowing users to receive immediate updates on camera events and system status within the Frigate ecosystem.

It provides support for automated workflows, allowing users to define and execute complex camera management tasks within the Frigate ecosystem.

It uses commands to interact with the Frigate ecosystem, allowing users to perform specific actions and control camera operations programmatically.

Status Codes:

- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error
- `403`: Forbidden

It returns a json response for all commands and operations, providing structured information about the status and results of the requested actions:

```json
{
    "status": "success",
    "message": "Image captured successfully",
    "status_code": 200,
    "data": {
        "camera_id": "camera_1",
        "image": "image_data"
    }
}
```

It works by sending commands to the Frigate ecosystem using the Model Context Protocol (MCP) and the Frigate Python library, allowing users to control and manage multiple cameras programmatically.
