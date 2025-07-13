# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Docker Development (Recommended)
- `docker compose up` - Start all services (web, worker, redis)
- `docker compose down` - Stop all services
- `docker compose build` - Rebuild containers after dependency changes

### Local Development
- `uv sync` - Install dependencies
- `uv run uvicorn app.main:app --host 0.0.0.0 --port 8150` - Start FastAPI server
- `uv run celery -A celery_src.celery_app worker --loglevel=info -O fair --concurrency=1 -Q sms` - Start Celery worker

### Database Migrations
- `aerich init-db` - Initialize database
- `aerich migrate` - Generate migrations
- `aerich upgrade` - Apply migrations

### Environment Setup
- Copy `env.example` to `.env` for local development
- Copy `env.docker_example` to `.env.docker` for Docker development
- Run ngrok pointing to port 8150 for webhook testing

## Architecture Overview

This is a FastAPI-based AI community management system with the following key components:

### Core Structure
- **FastAPI Application** (`app/main.py`) - Main web server with router registration
- **Tortoise ORM** - Database abstraction layer with SQLite/PostgreSQL support
- **Celery** - Async task processing with Redis broker
- **Twilio Integration** - SMS/WhatsApp messaging capabilities

### Key Models (`app/models/model.py`)
- **Client** - Organizations using the system (has AI phone number and bot name)
- **Lead** - Individuals being contacted (associated with clients)
- **Campaign** - Marketing campaigns linking clients to leads
- **Conversation** - SMS/message threads between leads and AI agents
- **Message** - Individual messages within conversations

### Service Architecture
- **Routers** (`app/routers/`) - API endpoint definitions for clients, leads, campaigns, SMS
- **Services** (`app/services/`) - Business logic, primarily SMS community support
- **Repository** (`app/repository/`) - Data access layer for each model
- **Tasks** (`app/tasks/`) - Celery background tasks for SMS processing
- **Library** (`app/library/`) - Utility functions for LLM, SMS, and Twilio operations

### Key Features
- AI-powered SMS conversations using OpenAI
- SMS blast campaigns to lead lists
- WhatsApp group management
- Community support automation
- Lead classification and follow-up scheduling

### Dependencies & Tech Stack
- Python 3.9+ with uv dependency management
- FastAPI for REST API
- Tortoise ORM for database operations
- Celery + Redis for background task processing
- Twilio for SMS/WhatsApp integration
- OpenAI for AI conversation capabilities

### Development Notes
- The system uses environment-based configuration (ENV variable controls docs visibility)
- Database migrations are handled through Aerich
- Background tasks are queued to 'sms' queue and processed by Celery workers
- API documentation is available at `/docs` in development mode