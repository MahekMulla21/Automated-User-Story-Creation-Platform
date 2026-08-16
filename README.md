# Automated User Story Creation Platform

An AI-based application developed to simplify the process of converting software requirements into structured User Stories and Acceptance Criteria.

The platform accepts software requirements as text or documents and uses Google Gemini to analyze the requirement and generate relevant Agile User Stories. It also supports requirements written in different languages by translating them into English before processing.

## Project Overview

In a typical software development process, converting detailed requirements into individual User Stories can take considerable time, especially when the requirement contains multiple functionalities.

This project aims to automate this initial step. Instead of generating only a single story from a requirement, the system analyzes the requirement and identifies different functional areas and features that can be converted into separate User Stories.

Each generated User Story can then be associated with its corresponding Acceptance Criteria.

## Key Features

- Accept software requirements through the application interface.
- Support requirements written in multiple languages.
- Automatically detect the language of the requirement.
- Translate non-English requirements into English.
- Use Google Gemini LLM for requirement analysis and generation.
- Generate multiple meaningful User Stories from complex requirements.
- Generate Acceptance Criteria for the generated stories.
- Process requirements provided through supported documents.
- Handle API and processing errors without exposing technical errors directly to users.
- Support deployment of the application as a web service.

## Multilingual Requirement Support

- Initially designed to accept English software requirements.
- Added a translation module for multilingual requirements.
- Detects the language automatically.
- Translates non-English requirements into English.
- Passes the translated requirement to the User Story generation pipeline.

## AI Integration

- Uses Google Gemini LLM for requirement analysis.
- Identifies relevant functional areas.
- Breaks complex requirements into smaller features.
- Generates multiple User Stories.
- Generates Acceptance Criteria for each story.
- Avoids unnecessary duplicate User Stories.
- Keeps generated content relevant to the original requirement.
- Includes retry and error-handling logic for temporary Gemini API failures.

## Document Processing

- Supports requirement input through supported documents.
- Extracts requirement content from documents.
- Passes extracted content through the same processing pipeline.
- Reduces the need for manually entering lengthy requirements.

## Testing

- Requirement input validation.
- Language detection testing.
- Translation testing.
- Multiple User Story generation testing.
- Acceptance Criteria testing.
- Document processing testing.
- Gemini API failure testing.
- Error-handling testing.
- End-to-end workflow testing.
- Deployment testing.
- Positive and negative test cases.

## Technologies Used

- Python
- Streamlit
- Google Gemini LLM
- Google GenAI SDK
- langdetect
- deep-translator
- MarkItDown
- Git
- GitHub
- Render

## Deployment

- Deployed as a Render Web Service.
- Uses environment variables for the Gemini API key.
- Start command:
  `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## Current Development Focus

- Generate multiple meaningful User Stories from a single complex requirement.
- Identify functional areas and features from requirements.
- Improve User Story coverage.
- Avoid duplicate or irrelevant stories.
- Generate Acceptance Criteria for each story.
- Prepare and execute project test cases.

## Future Improvements

- Epic and Feature level classification.
- User Story prioritization.
- Duplicate Story detection.
- Requirement-to-Story traceability.
- Story point estimation.
- Automated test case generation.
- Export to Excel and other formats.
- Integration with project management tools.

## Project Objective

- Convert software requirements into structured User Stories and Acceptance Criteria.
- Reduce manual effort in the requirements analysis process.
- Improve coverage of complex software requirements using AI.

## Author

**Mahek Mulla**

BE Computer Engineering
Python • Streamlit • Google Gemini • langdetect • deep-translator • MarkItDown • Git • GitHub • Render

