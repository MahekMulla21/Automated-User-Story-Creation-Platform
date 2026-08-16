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

**Multilingual Requirement Support:**

The application was initially designed to work with English software requirements. A translation module was later added to allow users to provide requirements in multiple languages.
The detected non-English requirement is translated into English before it is passed to the User Story generation process.

**AI Integration:**

Google Gemini is used as the main language model for requirement analysis and User Story generation.

The application uses structured prompts to guide the model to:

Understand the given requirement.
Identify relevant functional areas.
Break complex requirements into smaller features.
Generate separate User Stories.
Generate Acceptance Criteria for the stories.
Avoid unnecessary duplicate stories.
Keep the generated content related to the original requirement.

Error handling and retry logic have also been added for temporary Gemini API failures.

**Document Processing:**

The application also includes document processing functionality for extracting requirement content from supported files.
The extracted content is passed through the same requirement processing pipeline so that users can work with requirements provided as documents instead of entering everything manually.

**Testing**

Testing is being carried out alongside development to verify the different modules of the application.

The test cases cover areas such as:

Requirement input validation
Language detection
Translation
Multiple User Story generation
Acceptance Criteria generation
Document processing
Gemini API failures
Error handling
End-to-end workflow
Deployment testing

Both valid and invalid inputs are considered while preparing the test cases.

**Technologies Used**

Language
Python
Application
Streamlit

AI
Google Gemini LLM
Google GenAI SDK
Translation & NLP
langdetect
deep-translator

Document Processing
MarkItDown

Version Control
Git
GitHub

**Deployment**

Example start command:
streamlit run app.py --server.port $PORT --server.address 0.0.0.0

Current Development Focus

The current development work is focused on improving the generation process so that a single complex software requirement can produce a complete set of meaningful User Stories rather than only one User Story.

Along with this, test cases are being prepared and executed to verify the correctness of the generated results and the overall application workflow.

Future Improvements

Some planned improvements include:

Epic and Feature level classification
User Story prioritization
Duplicate story detection
Requirement-to-story traceability
Story point estimation
Automated test case generation
Exporting generated stories to Excel or other formats
Integration with project management tools

Author

Mahek Mulla

BE Computer Engineering

An AI-based application that converts software requirements into User Stories and Acceptance Criteria using Google Gemini LLMs.

Features
AI-based requirement analysis
Generates multiple meaningful User Stories
Generates Acceptance Criteria
Supports multilingual requirements with English translation
Supports document-based requirements
Error handling and Gemini API retry mechanism
Test case development and validation
Deployable using Render
Tech Stack

Python • Streamlit • Google Gemini • langdetect • deep-translator • MarkItDown • Git • GitHub • Render

