from ollama import chat


def generate_remark(glucose, hemoglobin, cholesterol):

    prompt = f"""
You are generating a patient report summary.

Lab Results:
- Glucose: {glucose}
- Hemoglobin: {hemoglobin}
- Cholesterol: {cholesterol}

Create a short factual summary of the values.
Do not provide a diagnosis.
Do not mention limitations.
Keep the response under 50 words.
"""
    response = chat(
        model='llama3.2:latest',
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ]
    )

    return response['message']['content']