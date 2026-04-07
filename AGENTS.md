# AGENTS.md

## Project Name
Corpus Preparation - RisetPajak

## Mission
Transform raw tax regulation documents into structured, AI-ready corpus.

## Objectives
- Extract text from PDF regulations
- Clean and normalize data
- Structure into legal hierarchy (pasal, ayat, huruf)
- Prepare for AI (embedding, semantic search)

## Pipeline Stages
1. Extract → PDF to raw text/table
2. Clean → remove noise, fix structure
3. Transform → map to pasal/ayat
4. Enrich → tagging + metadata
5. Output → JSON corpus

## Core Rules
- Never skip validation step
- Always preserve original text
- Never overwrite raw data
- Always log transformation steps

## Agent Workflow
- Read TASKS.md
- Check SCHEMA.md before modifying structure
- Log all changes in memory/YYYY-MM-DD.md
- Update MEMORY.md only for stable patterns

## Data Principles
- Accuracy > completeness
- Structure > raw text
- Traceability is mandatory

## Safety Rules
- Never fabricate regulation content
- If parsing fails → mark as "unparsed"
