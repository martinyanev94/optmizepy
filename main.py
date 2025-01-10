import os
import re
import ast
from typing import List

# Initialize a global token counter
total_chat_gpt_tokens_used = 0


# ChatGPT function definition
def chat_gpt(prompt: str, model: str = "gpt-4o-mini"):
    global total_chat_gpt_tokens_used
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": f"{prompt}"}
        ],
    )
    total_chat_gpt_tokens_used += response.usage.total_tokens
    return response.choices[0].message.content


# Function to extract Python functions from a file
def extract_functions(file_content: str) -> List[ast.FunctionDef]:
    try:
        tree = ast.parse(file_content)
        return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    except SyntaxError as e:
        print(f"Syntax error while parsing file: {e}")
        return []


# Function to get the source code of a function
def get_function_source(func: ast.FunctionDef, file_content: str) -> str:
    lines = file_content.splitlines()
    return "\n".join(lines[func.lineno - 1:func.end_lineno])


# Function to optimize a Python function using ChatGPT
def optimize_function(function_code: str) -> str:
    prompt = (
        f"Here is a Python function. Please reduce its size while maintaining its functionality:\n\n"
        f"{function_code}"
    )
    optimized_code = chat_gpt(prompt)
    return optimized_code


# Function to test an optimized function
def test_function(original_code: str, optimized_code: str):
    # Get example inputs and expected output using ChatGPT
    prompt_input = (
        f"For the following Python function, provide a sample input and expected output:\n\n"
        f"{original_code}"
    )
    io_data = chat_gpt(prompt_input)

    try:
        example_input, expected_output = eval(io_data)

        # Test the optimized function
        exec_globals = {}
        exec(optimized_code, exec_globals)

        function_name = re.search(r"def (\w+)\(", optimized_code).group(1)
        optimized_function = exec_globals[function_name]

        actual_output = optimized_function(*example_input)

        if actual_output == expected_output:
            print(f"Function {function_name} passed the test!")
        else:
            print(f"Function {function_name} failed the test.")
            print(f"Expected: {expected_output}, but got: {actual_output}")

    except Exception as e:
        print(f"Error testing function: {e}")


# Main function to process all files in a directory
def process_directory(directory: str):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                with open(file_path, "r") as f:
                    file_content = f.read()

                functions = extract_functions(file_content)
                for func in functions:
                    original_code = get_function_source(func, file_content)
                    optimized_code = optimize_function(original_code)
                    test_function(original_code, optimized_code)


if __name__ == "__main__":
    directory_to_analyze = input("Enter the directory to analyze: ")
    process_directory(directory_to_analyze)
    print(f"Total ChatGPT tokens used: {total_chat_gpt_tokens_used}")