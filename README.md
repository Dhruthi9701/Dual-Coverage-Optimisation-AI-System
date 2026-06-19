# DuCO-Agent: Dual Coverage Optimization Agent

An agentic, multi-modal AI system for Coordination of Benefits (COB)
across dual health insurance plans.

## Problem
Priya and Aarav Sen have dual health insurance coverage.
This system determines primary vs secondary payer, calculates
out-of-pocket costs, and generates pre-authorization letters.

## Structure
- `src/agents/` - Agentic reasoning modules
- `src/tools/` - Mock API tools and OCR utilities
- `src/engine/` - COB logic and calculation engine
- `src/utils/` - Helper functions
- `data/mock_inputs/` - Simulated input files

## Tech Stack
- Python 3.10+
- Claude / OpenAI API for vision and reasoning
- PyMuPDF for PDF parsing
- Pillow + Pytesseract for image OCR

## Branch Strategy
All development happens on feature branches.
No direct commits to main.