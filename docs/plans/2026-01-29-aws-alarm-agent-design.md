# AWS Alarm Agent - Design Document

## Overview

Un AI Agent per AWS che viene attivato quando scattano allarmi CloudWatch. L'agente ha permessi di lettura e può analizzare configurazioni e metriche di tutti i servizi AWS per identificare la causa principale del problema, generando un report inviabile via email.

**Business Model:** Open-core
- **Open Source:** Agente standalone per self-hosting
- **SaaS a pagamento:** Piattaforma multi-tenant con dashboard, onboarding guidato, analytics

## Architettura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ACCOUNT CLIENTE                                   │
│  ┌──────────────┐      ┌──────────────────┐      ┌───────────────────────┐  │
│  │  CloudWatch  │─────▶│  EventBridge     │─────▶│  EventBridge Rule     │  │
│  │  Alarm       │      │  (alarm event)   │      │  (forward to your     │  │
│  └──────────────┘      └──────────────────┘      │   Event Bus)          │  │
│                                                   └───────────┬───────────┘  │
│  ┌──────────────────────────────────────────┐                 │              │
│  │  IAM Role (read-only, cross-account)     │                 │              │
│  │  - AssumeRole dal tuo account            │                 │              │
│  │  - Permessi solo sui servizi scelti      │                 │              │
│  └──────────────────────────────────────────┘                 │              │
└───────────────────────────────────────────────────────────────┼──────────────┘
                                                                │
                                                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                              TUO ACCOUNT (Multi-tenant)                       │
│                                                                               │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐    │
│   │  EventBridge    │────▶│  Lambda         │────▶│  Bedrock Agent      │    │
│   │  (Event Bus)    │     │  (Orchestrator) │     │  (Claude Sonnet)    │    │
│   └─────────────────┘     └────────┬────────┘     └──────────┬──────────┘    │
│                                    │                         │               │
│                                    ▼                         ▼               │
│                           ┌─────────────────┐     ┌─────────────────────┐    │
│                           │  DynamoDB       │     │  Tool Functions     │    │
│                           │  - Clienti      │     │  (Lambda)           │    │
│                           │  - Allarmi      │     │  - GetMetrics       │    │
│                           │  - Report       │     │  - DescribeResource │    │
│                           └─────────────────┘     │  - GetConfig        │    │
│                                    ▲              └──────────┬──────────┘    │
│   ┌─────────────────┐              │                         │               │
│   │  SNS            │◀─────────────┴─────────────────────────┘               │
│   │  (Email report) │                                                        │
│   └─────────────────┘                                                        │
│                                                                               │
│   ┌─────────────────────────────────────────────────────────────────────────┐│
│   │  PORTALE WEB                                                            ││
│   │  - API Gateway + Lambda (backend)                                       ││
│   │  - S3 + CloudFront (frontend React)                                     ││
│   │  - Cognito (auth)                                                       ││
│   └─────────────────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────────────────┘
```

### Flusso Principale

1. Allarme scatta nell'account cliente → evento arriva al tuo EventBridge
2. Lambda orchestrator riceve l'evento, identifica il cliente, recupera le sue configurazioni
3. Invoca Bedrock Agent che usa i tool per investigare (assumendo il role cross-account del cliente)
4. Agent produce report → salvato in DynamoDB → inviato via SNS/email

## Componente Open Source

### Struttura Repository

```
aws-alarm-agent/
├── src/
│   ├── agent/
│   │   ├── prompts/           # System prompt e istruzioni per Claude
│   │   └── orchestrator.py    # Logica principale dell'agente
│   ├── tools/                 # Tool che l'agente può invocare
│   │   ├── cloudwatch.py      # GetMetricData, DescribeAlarms
│   │   ├── ec2.py             # DescribeInstances, DescribeVolumes
│   │   ├── rds.py             # DescribeDBInstances, logs
│   │   ├── lambda_.py         # GetFunction, logs da CloudWatch
│   │   ├── ecs.py             # DescribeServices, DescribeTasks
│   │   └── ...                # Un file per servizio AWS
│   ├── output/
│   │   ├── formatters.py      # Markdown, HTML, JSON
│   │   └── email.py           # Formattazione email
│   └── config.py              # Configurazione (quali servizi abilitare)
├── infrastructure/
│   ├── terraform/             # Deploy self-hosted
│   └── cloudformation/        # Alternativa CFN
├── examples/
│   └── alarms/                # Esempi di allarmi e output
├── docs/
└── README.md
```

### Funzionamento Agente

1. Riceve payload allarme (JSON CloudWatch)
2. Estrae: servizio coinvolto, metrica, threshold, risorsa
3. Chiama Bedrock con tool use - l'agente decide quali API chiamare
4. Itera finché non ha abbastanza contesto
5. Genera report strutturato

### Deploy Self-Hosted

- 1 Lambda (l'agente)
- 1 EventBridge Rule (trigger)
- IAM Role per Bedrock + servizi da monitorare
- Opzionale: SNS per email

## Componente SaaS

### Backend API

```
API Gateway + Lambda (Python/Node)
│
├── POST /customers              # Onboarding nuovo cliente
├── GET  /customers/:id          # Dettagli cliente
├── PUT  /customers/:id/config   # Configura servizi monitorati
│
├── POST /customers/:id/role     # Valida IAM Role cross-account
├── GET  /customers/:id/alarms   # Lista allarmi ricevuti
├── GET  /customers/:id/reports  # Storico report generati
│
└── POST /webhooks/eventbridge   # Riceve eventi dai clienti
```

### Database (DynamoDB)

```
Tabella: Customers
- PK: customer_id
- email, company_name, created_at
- role_arn (IAM Role cross-account)
- allowed_services: ["ec2", "rds", "lambda", ...]
- notification_config: {email: [...], slack_webhook: "..."}

Tabella: AlarmEvents
- PK: customer_id
- SK: timestamp#alarm_id
- alarm_payload, status, report_id

Tabella: Reports
- PK: report_id
- customer_id, alarm_id, created_at
- content (il report generato)
- tokens_used, cost
```

### Portale Web

**Stack:**
- React + Vite (frontend)
- Tailwind CSS (styling)
- S3 + CloudFront (hosting)
- Amazon Cognito (auth)

### Flusso Onboarding Cliente

1. Signup sul portale (email + password)
2. Wizard: selezione servizi da monitorare
3. Generazione automatica policy IAM (con opzione CloudFormation one-click)
4. Cliente inserisce Role ARN → validazione con STS AssumeRole
5. Setup EventBridge (con opzione CloudFormation one-click)
6. Test: invio allarme di test per verificare il flusso

## Stima Costi

**Per 50 clienti, ~2000 allarmi/mese:**

| Servizio | Utilizzo | Costo stimato/mese |
|----------|----------|-------------------|
| Bedrock (Sonnet) | ~2000 invocazioni, ~3K tokens in + ~1K out | ~$25-40 |
| Lambda | ~10K invocazioni | < $1 |
| DynamoDB | On-demand, ~100K read/write | < $5 |
| EventBridge | ~2000 eventi | < $1 |
| API Gateway | ~50K requests | < $5 |
| S3 + CloudFront | Hosting frontend | < $5 |
| Cognito | 50 utenti attivi | Gratis |
| SNS | ~2000 email | < $1 |
| **Totale** | | **~$40-60/mese** |

### Ottimizzazioni

- Lambda con ARM64 (Graviton) - 20% più economico
- DynamoDB on-demand - paghi solo l'uso reale
- Niente NAT Gateway - Lambda accede via VPC endpoints o internet pubblico
- Cache contesto cliente - evita read DynamoDB ripetute

## Piano di Sviluppo

### Fase 1 - MVP Open Source

- Agente standalone per singolo account
- 3-5 servizi AWS supportati (EC2, RDS, Lambda, ECS, ALB)
- Output report via email/stdout
- Deploy con Terraform/CloudFormation
- Documentazione ed esempi

### Fase 2 - MVP SaaS

- Backend multi-tenant (API, DynamoDB)
- Portale base: signup, onboarding wizard, lista report
- Cross-account IAM + EventBridge setup
- Billing manuale

### Fase 3 - Crescita

- Dashboard analytics (trend, servizi problematici)
- Integrazioni (Slack, PagerDuty, Teams)
- Più servizi AWS supportati
- Stripe per billing automatico

## Decisioni Tecniche

| Aspetto | Scelta | Motivazione |
|---------|--------|-------------|
| Deployment | Multi-tenant centralizzato | Dashboard centralizzata, costi ottimizzati, manutenzione semplice |
| Trigger | EventBridge cross-account | Moderno, filtraggio potente, event-driven |
| Modello AI | Claude Sonnet su Bedrock | Bilanciamento costo/qualità, ottimo tool use |
| Database | DynamoDB on-demand | Serverless, scala automaticamente, pay-per-use |
| Frontend | React + Vite + Tailwind | Leggero, veloce, pragmatico |
| Auth | Cognito | Integrato AWS, gestisce email verification |
| Business model | Open-core | Adoption tramite OSS, revenue da SaaS |

## Differenziazione da Soluzioni Esistenti

- **Amazon DevOps Guru:** ML per anomalie, ma non ragiona né spiega. Insight predefiniti.
- **Amazon Q Developer:** Orientato al codice, non troubleshooting infrastrutturale real-time.

**Valore unico:** Un agente AI che ragiona attivamente su un allarme, esplora metriche correlate, e produce un report human-readable con root cause analysis.
