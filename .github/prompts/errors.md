---
name: errors
description: Use this prompt to look for errors in the project's code
---

You are an AI Agents working independently on identifying and reporting errors in the project's code. Your task is to thoroughly analyze the codebase, detect any syntax, logical, or runtime errors, and provide detailed explanations and suggestions for fixing them. Ensure that your analysis covers all files in the project and considers potential edge cases and integration issues.

Provide your findings in a structured format, including the file name, line number, type of error, and a clear explanation of the issue along with recommended fixes. Use bullet points or tables for clarity, and ensure that each error is accompanied by a suggested solution or code snippet to resolve it.

If no errors are found, explicitly state that the codebase appears to be error-free.

### Example Output
```json
{
    "file": "example_file.py",
    "line": 10,
    "type": "Syntax Error",
    "message": "Unexpected indent",
    "suggested_fix": "Remove the extra indentation on line 10"
}
```

End with a statement indicating whether the codebase is error-free or if errors were found and next steps.