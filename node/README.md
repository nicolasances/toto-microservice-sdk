# Toto Microservice SDK - NodeJS

The Toto Microservice SDK is a framework for building cloud-agnostic microservices. <br>
This is the NodeJS SDK documentation. 

## Table of Contents

1. [Installation](#1-installation)
2. [Overview](#2-overview)
3. [Usage](#3-usage)
   - [3.1. The Toto Microservice Configuration](#31-the-toto-microservice-configuration)
   - [3.2. Create and Register APIs](#32-create-and-register-apis)
   - [3.3. Use a Message Bus](#33-use-a-message-bus)
   - [3.4. Load Secrets](#34-load-secrets)
   - [3.5. Custom Configurations](#35-custom-configurations)

Other: 
* [Build and Deploy on NPM](./docs/buildpublish.md)

## 1. Installation

```bash
npm install totoms
```

### Cloud-Specific Dependencies

Install the peer dependencies for your target cloud platform:

**AWS:**
```bash
npm install @aws-sdk/client-secrets-manager @aws-sdk/client-sns @aws-sdk/client-sqs
```

**GCP:**
```bash
npm install @google-cloud/pubsub @google-cloud/secret-manager
```

## 2. Overview

Everything starts with `TotoMicroservice` and the `TotoMicroserviceConfiguration`.<br>
`TotoMicroservice` is the main orchestrator that coordinates your entire microservice. It initializes and manages:

- **API Controller & API Endpoints**: Express-based REST API setup with automatic endpoint registration
- **Message Bus & Message Handlers**: Event-driven communication via Pub/Sub and Queues. Registration and routing of event handlers to appropriate topics.
- **Secrets Management**: Automatic loading of secrets from your cloud provider
- **Service Lifecycle**: Initialization, startup, and shutdown management

The configuration is **declarative**. The goal is to make it very simple to configure a full microservice, with a syntax that will look like this:

```typescript
import { getHyperscalerConfiguration, SupportedHyperscalers, TotoMicroservice, TotoMicroserviceConfiguration } from 'totoms';
import { ControllerConfig } from "./Config";
import { SayHello } from './dlg/ExampleDelegate';


const config: TotoMicroserviceConfiguration = {
    serviceName: "toto-ms-ex1",
    basePath: '/ex1',
    environment: {
        hyperscaler: process.env.HYPERSCALER as SupportedHyperscalers || "aws",
        hyperscalerConfiguration: getHyperscalerConfiguration()
    },
    customConfiguration: ControllerConfig,
    apiConfiguration: {
        apiEndpoints: [
            { method: 'GET', path: '/hello', delegate: SayHello }
        ],
        apiOptions: { noCorrelationId: true }
    }, 
};

TotoMicroservice.init(config).then(microservice => {
    microservice.start();
});
```

A **few things you should pay attention to**: 
* `ControllerConfig` - that's your custom configuration class, that you can use to do any type of custom initialization and work (e.g. loading secrets). <br>
You can find [more details in this section](#31-the-toto-microservice-configuration)

The `TotoMicroserviceConfiguration` object specifies:

- **Service Metadata**: Service name and base path for API endpoints
- **Environment**: Cloud provider (AWS, GCP, Azure) information
- **API Configuration**: REST endpoints with their handlers
- **Message Bus Configuration**: Topics to subscribe to and message handlers
- **Custom Configuration**: Your application-specific settings

## 3. Usage

### 3.1. The Toto Microservice Configuration

The microservice is configured through the `TotoMicroserviceConfiguration` object and the `TotoControllerConfig` base class. <br>
As seen above, you need to define a **Custom Configuration Class** that extends the `TotoControllerConfig` base class as shown below here. 

```typescript
import { TotoControllerConfig } from 'totoms';

export class ControllerConfig extends TotoControllerConfig {

    getMongoSecretNames(): { userSecretName: string; pwdSecretName: string; } | null {
        return null;
    }

    getProps(): APIOptions {
        return {}
    }

}
```

Some things to **note**: 
* The `getMongoSecretNames()` method allows you to define the name of the Secrets containing user and pswd of your Mongo DB, if you choose to use it (stored in the Cloud Secrets Manager, depending on the cloud you're deploying to). 
* The `getProps()` method allows you to do some overrides (e.g. no authentication for this service). You can explore the properties, they're well documented in the SDK.

### 3.2. Create and Register APIs

Your microservice exposes REST API endpoints using Express. <br>
Endpoints are defined when creating the API controller and are automatically set up.

#### Create a Toto Delegate

Every endpoint needs to be managed by a **Toto Delegate**. <br>
Toto Delegates implement the `TotoDelegate` interface.

This is how you define a Toto Delegate. <br>
*The following example shows a delegate that processes user creation*.

```typescript
import { TotoDelegate, UserContext } from 'totoms';
import { Request } from 'express';

class CreateUserDelegate extends TotoDelegate {

    async do(req: Request, userContext?: UserContext): Promise<any> {

        // Extract data from the request
        const { name, email } = req.body;
        
        // Your business logic here
        ...
        
        // Return the response (anything you'd like)
        return { 
            ..., 
        };
    }
}
```

#### Register Your Delegate
You can now register your delegate with its endpoint (path, route) in the `TotoMicroserviceConfiguration` object that we saw earlier. 

```typescript
const config: TotoMicroserviceConfiguration = {
    serviceName: "toto-ms-ex1",
    basePath: '/ex1',
    environment: ...,
    ...
    apiConfiguration: {
        apiEndpoints: [
            { method: 'POST', path: '/users', delegate: CreateUserDelegate }
        ]
    }, 
};
```

---

### 3.3. Use a Message Bus

The Message Bus enables event-driven communication between microservices.<br>
It supports both PUSH (webhook-based from cloud Pub/Sub) and PULL (polling) delivery models, depending on your cloud provider and configuration.

#### 3.3.1. React to Messages

Message handlers are the primary way to react to events.

##### Create a Message Handler

Create a handler by **extending** `TotoMessageHandler` and implementing the required methods:

```typescript
import { TotoMessageHandler, TotoMessage, ProcessingResponse } from 'totoms';

class TopicRefreshedEventHandler extends TotoMessageHandler {
    
    getHandledMessageType(): string {
        // Return the message type this handler processes
        return "topicRefreshed";
    }
    
    async processMessage(message: TotoMessage): Promise<ProcessingResponse> {
        // Access message metadata
        const correlationId = message.correlationId;
        const messageId = message.id;
        
        // Extract event data
        const topicName = message.payload.name;
        const blogUrl = message.payload.blogURL;
        const user = message.payload.user;
        
        // Your handler has access to context
        this.logger.compute(correlationId, `Processing topic refresh for: ${topicName}`);
        
        // Perform your business logic
        await this.refreshTopic(topicName, blogUrl, user);
        
        // Return success or failure
        return { success: true };
    }
    
    private async refreshTopic(name: string, url: string, user: string) {
        // Implementation here
    }
}
```

##### Register a Message Handler

Register your message handlers with the message bus configuration.

**IMPORTANT NOTE:** <br>
* When using PubSub infrastructure, you need to register topics. <br>
Topics are registered by giving them:
    * A `logical name` which is the name that will be used in the application to reference the topic.
    * A topic identifier (e.g., ARN on AWS or fully-qualified Topic Name on GCP)

```typescript
import { TotoMessageBus, MessageHandlerRegistrationOptions } from 'totoms';

const messageBus = new TotoMessageBus(config, environment);

// Register topics
messageBus.registerTopic({
    logicalName: "topic-events",
    topicName: process.env.TOPIC_EVENTS_TOPIC_NAME! // From environment or secrets
});

// Register message handlers
const handlerOptions: MessageHandlerRegistrationOptions = {
    topic: { logicalName: "topic-events" }
};

messageBus.registerMessageHandler(
    new TopicRefreshedEventHandler(),
    handlerOptions
);
```

When the microservice starts, it automatically subscribes to the configured topics and routes incoming messages to the appropriate handlers based on their message type.

#### 3.3.2. Publish Messages

You can always publish messages to topics.

**NOTE:**
* In the Message Destination, the topic is the **logical name of the topic** (see above).

```typescript
import { TotoMessage, MessageDestination } from 'totoms';

async function publishTopicUpdate(messageBus: any, topicId: string, topicName: string) {
    // Create the message
    const message = new TotoMessage({
        type: "topicUpdated",
        correlationId: "correlation-id-123",
        id: topicId,
        payload: { 
            name: topicName, 
            timestamp: new Date().toISOString() 
        }
    });
    
    const destination: MessageDestination = { 
        topicName: "topic-events" 
    };

    await messageBus.publishMessage(destination, message);
}
```

##### Getting Access to the Message Bus

There are different ways to get access to the Message Bus instance:

* Through the `TotoMicroservice` singleton: <br>
`TotoMicroservice.getInstance().messageBus`

* Through an existing instance of `TotoMicroservice`

* In a `TotoMessageHandler` you will have `messageBus` as an instance variable: <br>
`this.messageBus`

* In a `TotoDelegate`, you can access it through the config or by maintaining a reference in your application

---

### 3.4. Load Secrets

The SDK handles secret loading from your cloud provider automatically. Access secrets through the configuration or use the `SecretsManager` directly:

```typescript
import { SecretsManager } from 'totoms';

const secrets = new SecretsManager({ hyperscaler: "aws" });

// Load a secret by name
const apiKey = await secrets.getSecret("api-key");
const databaseUrl = await secrets.getSecret("database-url");
```

Secrets are typically stored as environment variable names or secret manager references, depending on your deployment environment.

---

### 3.5. Custom Configurations

You can define your own custom configurations by extending the `TotoControllerConfig` base class.

An example:

```typescript
import { TotoControllerConfig } from 'totoms';

export class MyServiceConfig extends TotoControllerConfig {
    
    apiKey: string | undefined;
    
    async load(): Promise<void> {
        // Load secrets using the secrets manager
        this.apiKey = await this.secretsManager.getSecret("my-api-key");
    }
    
    getMongoSecretNames() {
        // Return null if your service doesn't use MongoDB
        return null;
    }
}
```

What you can do with a Custom Configuration:

1. **Load Secrets** <br>
You can do that by overriding the `load()` async method and using `this.secretsManager.getSecret("your-secret-name")` to load secrets.

2. **Configure MongoDB** <br>
Override `getMongoSecretNames()`, `getDBName()`, and `getCollections()` to configure MongoDB integration.

3. **Custom Authentication** <br>
Override `getCustomAuthVerifier()` to provide custom authentication logic.

## Core Components

### TotoAPIController
The main controller for building REST APIs with Express. Provides:
- Automatic route registration
- Built-in validation
- CORS support
- Health check endpoints
- File upload support
- API documentation generation

### TotoMicroservice
High-level wrapper that initializes the entire microservice stack including API controller, message bus, and environment configuration.

### TotoMessageBus
Unified interface for pub/sub messaging across cloud platforms:
- **AWS**: SNS/SQS
- **GCP**: Cloud Pub/Sub
- **Azure**: Service Bus (in development)

### TotoControllerConfig
Base configuration class for microservices with support for:
- MongoDB connection management
- Authentication settings
- Secrets management
- Custom validators

### Logger
Structured logging with correlation ID support for request tracing.

### Validator
Request validation framework with support for:
- JWT token validation
- Google OAuth
- Custom validation logic

## Cloud Platform Support

### AWS
- **Messaging**: SNS (topics), SQS (queues)
- **Secrets**: AWS Secrets Manager
- **Region Configuration**: Configurable per service

### GCP
- **Messaging**: Cloud Pub/Sub
- **Secrets**: Secret Manager
- **Project Configuration**: Uses default project credentials

### Azure
- **Messaging**: Service Bus (in development)
- **Secrets**: Key Vault (in development)

## License

MIT

## Author

nicolasances

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request to the [toto-microservice-sdk repository](https://github.com/nicolasances/toto-microservice-sdk).

## Related Projects

- [Toto Ecosystem](https://github.com/nicolasances/toto)
- [Python Toto Microservice SDK](../python)
