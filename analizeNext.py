import ast

# Read the content of the uploaded file
file_path = '../../next.py'
with open(file_path, 'r') as file:
    file_content = file.read()

# Parse the content of the file
parsed_ast = ast.parse(file_content)

# Initialize a dictionary to store function calls
function_calls = {}

class FunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.current_function = None
    
    def visit_FunctionDef(self, node):
        self.current_function = node.name
        function_calls[self.current_function] = []
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and self.current_function:
            function_calls[self.current_function].append(node.func.id)
        self.generic_visit(node)

# Visit all nodes in the AST
visitor = FunctionVisitor()
visitor.visit(parsed_ast)

# Filter only the functions defined in the file
defined_functions = set(function_calls.keys())

# Sort functions based on the order of calling
sorted_function_calls = sorted(
    [(func, [call for call in calls if call in defined_functions])
     for func, calls in function_calls.items()],
    key=lambda item: item[0]
)

# Print the sorted function calls
for function, calls in sorted_function_calls:
    if function != "main":
    #print(f"Function '{function}' calls: {', '.join(calls) if calls else 'No calls'}")
      print(f"Function '{function}' calls:")
      for func in calls:
        print(f"\t{func}")
for function, calls in sorted_function_calls:
    if function == "main":
    #print(f"Function '{function}' calls: {', '.join(calls) if calls else 'No calls'}")
      print(f"Function '{function}' calls:")
      for func in calls:
        print(f"\t{func}")
