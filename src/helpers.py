import ast
import re

def label_values(input_string,map):
    values = input_string.split(',')
    if isinstance(map,str):
        map = ast.literal_eval(map)
    labeled_values = [f"{v}: {map[v]}" for v in values]
    return ', '.join(labeled_values)

def first_non_empty_line(string):
  lines = string.splitlines()
  for line in lines:
    if line:
      return line

  return None

def extract_propositional_symbols(logical_form):
    symbols = re.findall(r'\b[a-z]\b', logical_form)
    return set(symbols)

def split_string_except_in_brackets(string, delimiter):
    result = []
    stack = []
    current = ''

    for char in string:
        if char == '(':
            stack.append('(')
        elif char == ')':
            if stack:
                stack.pop()
        if char == delimiter and not stack:
            result.append(current)
            current = ''
        else:
            current += char

    if current:
        result.append(current)

    return result

def remove_text_after_last_parenthesis(input_string):
    last_paren_index = input_string.rfind(')')
    if last_paren_index != -1:
        result = input_string[:last_paren_index+1]
        return result.strip()
    else:
        return input_string

def fix_inconsistent_arities(clauses1, clauses2):
    all_clauses = clauses1 + clauses2
    predicates = {}
    for clause in all_clauses:
        predicate = clause.split('(')[0]
        arity = len(clause.split(','))
        
        if predicate in predicates:
            if predicates[predicate] != arity:
                predicates[predicate] = min(predicates[predicate], arity)
        else:
            predicates[predicate] = arity
        fixed_clauses1 = []
    fixed_clauses2 = []
    for clause in clauses1:
        predicate = clause.split('(')[0]
        args = clause.split('(')[1].split(')')[0].split(',')
        arity = len(args)
        
        if arity > predicates[predicate]:
            new_clause = f"{predicate}({', '.join(args[:predicates[predicate]])})"
            fixed_clauses1.append(new_clause)
        else:
            fixed_clauses1.append(clause)
    
    for clause in clauses2:
        predicate = clause.split('(')[0]
        args = clause.split('(')[1].split(')')[0].split(',')
        arity = len(args)
        
        if arity > predicates[predicate]:
            new_clause = f"{predicate}({', '.join(args[:predicates[predicate]])})"
            fixed_clauses2.append(new_clause)
        else:
            fixed_clauses2.append(clause)
    
    return ', '.join(fixed_clauses1), ', '.join(fixed_clauses2)

def replace_variables(mapping, clause):
    reversed_mapping = {v: k for k, v in mapping.items()}
    replaced_clause = clause
    predicate = clause.split('(')[0]
    args = clause.split('(')[1][:-1].split(',')
    replaced_args=[]
    for arg in args:
        if arg in reversed_mapping:
            replaced_args.append(reversed_mapping[arg])
        else:
            replaced_args.append(arg)
    args=','.join(replaced_args)
    replaced_clause=predicate+'('+args+')'
    return replaced_clause

def substitute_variables(clause1,clause2,start_char):
    variables={}
    replaced_clause1 = clause1
    predicate = clause1.split('(')[0]
    args = clause1.split('(')[1][:-1].split(',')
    current_char = start_char
    replaced_args = []
    for arg in args:
        if arg not in variables:
            variables[arg]=current_char
            current_char = chr(ord(current_char) + 1)
        replaced_args.append(variables[arg])
    args=','.join(replaced_args)
    replaced_clause1=predicate+'('+args+')'
    replaced_clause2 = clause2
    predicate = clause2.split('(')[0]
    args = clause2.split('(')[1][:-1].split(',')
    replaced_args = []
    for arg in args:
        if arg not in variables:
            variables[arg]=current_char
            current_char = chr(ord(current_char) + 1)
        replaced_args.append(variables[arg])
    args=','.join(replaced_args)
    replaced_clause2=predicate+'('+args+')'
    return replaced_clause1, replaced_clause2, current_char