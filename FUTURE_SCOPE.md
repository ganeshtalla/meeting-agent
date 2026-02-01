# Future Scope & TODOs

This document outlines planned improvements and alternative integrations for the Meeting Agent project.

---

## Transcription Alternatives (Whisper Replacements)

Currently using OpenAI Whisper locally, which requires significant compute resources. Consider these cloud-based alternatives for easier deployment and better scalability:

### Cloud Speech-to-Text Services

| Service | Pros | Cons |
|---------|------|------|
| **AssemblyAI** | Excellent accuracy, speaker diarization, real-time streaming | Paid API |
| **Deepgram** | Fast, affordable, good for real-time | Requires API key |
| **Google Cloud Speech-to-Text** | Multi-language support, speaker diarization | Pay-per-use pricing |
| **AWS Transcribe** | Good AWS integration, batch processing | AWS ecosystem lock-in |
| **Azure Speech Services** | Enterprise features, custom models | Microsoft ecosystem |
| **Rev.ai** | Human-level accuracy, async processing | Higher cost |
| **OpenAI Whisper API** | Same model, cloud-hosted | Simpler than local setup |

### TODOs

- [ ] Add AssemblyAI integration as primary cloud alternative
- [ ] Implement Deepgram for real-time transcription use cases
- [ ] Add OpenAI Whisper API option (cloud-hosted version)
- [ ] Create unified transcription interface to swap providers easily
- [ ] Add provider selection in frontend settings
- [ ] Implement fallback mechanism (cloud -> local)

---

## LLM Alternatives (Ollama Replacements)

Currently supports Ollama (local), OpenAI, and Anthropic. Consider expanding integrations:

### Cloud LLM Providers

| Provider | Models | Best For |
|----------|--------|----------|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4-turbo | General purpose, high quality |
| **Anthropic** | Claude Opus 4, Claude Sonnet 4 | Long context, detailed analysis |
| **Google Gemini** | Gemini 1.5 Pro, Gemini 1.5 Flash | Multi-modal, long context |
| **Groq** | Llama 3, Mixtral | Ultra-fast inference |
| **Together AI** | Open source models | Cost-effective, variety |
| **Fireworks AI** | Fine-tuned models | Low latency |
| **Cohere** | Command R+ | Enterprise RAG |
| **Mistral AI** | Mistral Large, Medium | European hosting |

### Local LLM Alternatives

| Runtime | Description |
|---------|-------------|
| **LM Studio** | GUI-based, easy model management |
| **llama.cpp** | Lightweight, CPU-friendly |
| **vLLM** | High-throughput serving |
| **LocalAI** | OpenAI-compatible API |
| **Jan** | Desktop app with local models |

### TODOs

- [ ] Add Google Gemini integration (long context for full transcripts)
- [ ] Implement Groq for faster inference option
- [ ] Add Together AI for cost-effective cloud option
- [ ] Create LLM provider abstraction layer for easy swapping
- [ ] Add model selection dropdown in frontend
- [ ] Implement streaming responses for all providers
- [ ] Add cost estimation per provider
- [ ] Support custom/fine-tuned models via API

---

## Additional Future Enhancements

### Processing Features
- [ ] Real-time meeting transcription (live capture)
- [ ] Speaker diarization (who said what)
- [ ] Sentiment analysis per speaker
- [ ] Automatic meeting scheduling integration (Google Calendar, Outlook)
- [ ] Multi-language support with auto-detection

### Export & Integration
- [ ] Notion integration for meeting notes
- [ ] Slack/Teams bot for sharing summaries
- [ ] Jira/Linear integration for auto-creating tickets from action items
- [ ] Email summary distribution
- [ ] PDF export with formatting

### Infrastructure
- [ ] Docker Compose for one-command deployment
- [ ] Kubernetes Helm chart
- [ ] Serverless deployment option (AWS Lambda, Vercel)
- [ ] Redis for job queue (replace in-memory)
- [ ] PostgreSQL support for production

### Security & Auth
- [ ] User authentication (OAuth, SSO)
- [ ] Role-based access control
- [ ] End-to-end encryption for recordings
- [ ] Audit logging

---

## Priority Roadmap

### Phase 1: Cloud Transcription
1. AssemblyAI integration
2. OpenAI Whisper API integration
3. Provider selection UI

### Phase 2: Expanded LLM Support
1. Google Gemini integration
2. Groq integration for speed
3. Streaming responses

### Phase 3: Production Readiness
1. Docker Compose setup
2. PostgreSQL migration
3. User authentication

---

## Contributing

Want to help implement any of these features? Check out our [Contributing Guidelines](README.md#contributing) and pick a TODO from this list!
