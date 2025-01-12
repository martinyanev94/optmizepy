import os
import re
import ast
import shutil
from typing import List
from openai import OpenAI
from config import api_key

client = OpenAI(api_key=api_key)

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
        f"Here is a Python function. Please reduce its size while maintaining its functionality. Return the optimized code only. Give me only the code nothing else. Dont add imports.Keep same function name. Do not use different libraries. Return as code block.:\n\n"
        f"{function_code}"
    )
    optimized_code = chat_gpt(prompt)
    lines = optimized_code.splitlines()
    if "```" in optimized_code:
        return "\n".join(lines[1:-1])
    else:
        return optimized_code


def create_directory_copy(source: str, destination: str):
    if os.path.exists(destination):
        shutil.rmtree(destination)
    shutil.copytree(source, destination)

def test_function(original_code: str, optimized_code: str):
    prompt_input = (
        f"""
        For the following Python function, provide a sample input. 
        Provide the input only. Put all input params on different lines with a '-' in front. 
        If the function does not have inputs do not give any example inputs. Here is an example of how you should provide the inputs:
        -[2,3,6]
        -'Apple'
        -True

        Here is the code I want you to create example inputs for:
        \n\n
        {original_code}
        """
    )
    response = chat_gpt(prompt_input)
    lines = response.split("\n")
    inputs = []

    for line in lines:
        if line.startswith("-"):
            inputs.append(ast.literal_eval(line[1:].strip()))

    exec_globals = {}
    exec(original_code, exec_globals)

    function_name = re.search(r"def (\w+)\(", original_code).group(1)
    original_function = exec_globals[function_name]

    try:
        expected_output = original_function(*inputs)
    except Exception as e:
        print(f"Error while running the original function: {e}")
        return False

    exec_globals = {}
    exec(optimized_code, exec_globals)
    optimized_function = exec_globals[function_name]

    try:
        actual_output = optimized_function(*inputs)
        return actual_output == expected_output
    except Exception as e:
        print(f"Error while running the optimized function: {e}")
        return False


# Add these global variables to track line counts
total_original_lines = 0
total_optimized_lines = 0


def process_directory(directory: str, dest_root: str):
    global total_original_lines, total_optimized_lines

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                optimized_file_path = os.path.join(dest_root, os.sep.join(root.split(os.sep)[1:]), file)

                with open(file_path, "r") as f:
                    file_content = f.read()

                # Extract imports and functions from the file
                import_lines = [line for line in file_content.splitlines() if
                                line.strip().startswith(('import ', 'from '))]
                functions = extract_functions(file_content)

                for func in functions:
                    original_code = get_function_source(func, file_content)
                    optimized_code = optimize_function(original_code)

                    # Update line counts
                    original_line_count = len(original_code.splitlines())
                    optimized_line_count = len(optimized_code.splitlines())
                    total_original_lines += original_line_count
                    total_optimized_lines += optimized_line_count

                    if test_function("\n".join(import_lines) + "\n" + original_code,
                                     "\n".join(import_lines) + "\n" + optimized_code):
                        print(f"Function {func.name} optimized successfully.")
                        with open(optimized_file_path, 'r') as opt_file:
                            file_content1 = opt_file.read()

                        file_content1 = file_content1.replace(original_code, optimized_code)

                        # Write the updated content back to the file
                        with open(optimized_file_path, 'w') as opt_file:
                            opt_file.write(file_content1)
                    else:
                        print(f"Function {func.name} optimization failed. Keeping the original code.")


# Main function updated to print line count summary
if __name__ == "__main__":
    directory_to_analyze = "TestFolder"
    output_directory = "OptimizedFolder"
    create_directory_copy(directory_to_analyze, output_directory)

    process_directory(directory_to_analyze, output_directory)


    print(f"Total ChatGPT tokens used: {total_chat_gpt_tokens_used}")
    print(f"Original total lines of code: {total_original_lines}")
    print(f"Optimized total lines of code: {total_optimized_lines}")
    print(f"Total lines removed: {total_original_lines - total_optimized_lines}")
