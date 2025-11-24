import re
import sys
bound_variables = set()
unbound_variables = {}
predicate_to_sort_map = {}

class Sort:
    def __init__(self, sort=None):
        self.sort = sort
    
    def getSort(self):
        return self.sort
    
    def setSort(self, sort):
        self.sort = sort
    
    def __repr__(self):
        return str(self.sort)

class Operator:
    def __init__(self, operator):
        self.operator = operator
        self.quantifier = ("exists" in operator or "forall" in operator)
        self.arity = 1 if operator == "not" or self.quantifier else 2
        self.priority = Operator.priority_values(operator)
        self.quanified_variable = self.operator.split(" ")[1].replace("(", "") if self.quantifier else None
    
    def getOperatorArity(self):
        return self.arity
    
    def __repr__(self):
        return self.operator

    def getPriority(self):
        return self.priority
    
    @staticmethod
    def priority_values(op):
        if op == "not":
            return 5
        elif "exists" in op or "forall" in op:
            return 4
        elif op == "and":
            return 3
        elif op == "or":
            return 2
        elif op in ["=>", "="]:
            return 1
        else:
            return 0

class Predicate:
    def __init__(self, predicate_name):
        self.name = predicate_name
        self.terms = []
        self.prefix_form = []
        self.sort = []

    def set_terms(self, terms):
        i = 0
        n_parenthesis = 0
        running_tokens = []
        while i < len(terms):
            if terms[i] == ',':
                if n_parenthesis == 0:
                    self.terms.append(CVCGenerator.process_tokens(running_tokens))
                    running_tokens = []
                else:
                    running_tokens.append(terms[i])
            else:
                if terms[i] == '(':
                    n_parenthesis += 1
                elif terms[i] == ')':
                    n_parenthesis -= 1
                running_tokens.append(terms[i])
            i += 1
        
        self.terms.append(CVCGenerator.process_tokens(running_tokens))

        for term in self.terms:
            self.prefix_form.append(CVCGenerator.generatePrefixFormula(term))
        
        self.find_sort()

    def find_sort(self):
        self.sort = []
        for term in self.terms:
            if len(term) == 1:
                if term[0] in bound_variables:
                    self.sort.append(Sort("BoundSet"))
                else:
                    if term[0] not in unbound_variables:
                        unbound_variables[term[0]] = Sort()
                    self.sort.append(unbound_variables[term[0]])
            else:
                self.sort.append(Sort("Bool"))
        
        self.unify_sort()
    
    def unify_sort(self):
        if self.name not in predicate_to_sort_map:
            predicate_to_sort_map[self.name] = self.sort
        else:
            cur_sort = predicate_to_sort_map[self.name]
            if len(cur_sort) != len(self.sort):
                raise Exception("Sorts of {0} is not consistent.".format(self.name))
            for i in range(len(cur_sort)):
                cur_sort[i] = self.unify(cur_sort[i], self.sort[i])

    def unify(self, sort1, sort2):
        sort1_sort = sort1.getSort() if sort1 else None
        sort2_sort = sort2.getSort() if sort2 else None
        if sort1_sort == sort2_sort:
            return sort1
        elif sort1_sort is None:
            sort1.setSort(sort2_sort)
            return sort2
        elif sort2_sort is None:
            sort2.setSort(sort1_sort)
            return sort1
        else:                         
            raise Exception("Sorts of {0} are not consistent".format(self.name))
            
    def __repr__(self):
        return  "(" + self.name + " " + " ".join(self.prefix_form) + ")"

def isOperator(op):
    operators = ["not", "and", "or", "->", "<->", "=>", "<=>", "="]
    return not isinstance(op, Predicate) and \
           (isinstance(op, Operator) or op in operators or "exists" in op or "forall" in op)


class CVCGenerator:
    def __init__(self, formula):
        bound_variables.clear()
        unbound_variables.clear()
        predicate_to_sort_map.clear()
        self.formula = formula
        self.tokens = self.tokenize()

    def tokenize(self):
        tokens = re.split(r'(\(|\)|\s|\bexists\b|\band\b|\bor\b|\bnot\b|\bforall\b|\->|<->|,|<=>|=>|=)', self.formula)
        result = []
        for token in tokens:
            if token not in ['', ' ']:
                if token == '->':
                    result.append("=>")
                elif token in ['<->', '<=>']:
                    result.append("=")
                else:
                    result.append(token)
        return CVCGenerator.process_tokens(result)
    
    @staticmethod
    def process_tokens(tokens):
        result = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if isOperator(token):
                if token in ["exists", "forall"]:
                    token = token + " " + tokens[i + 1]
                    bound_variables.add(tokens[i + 1])
                    i += 1

                result.append(Operator(token))
            else:
                if i + 1 < len(tokens) and tokens[i + 1] == '(':
                    pred = Predicate(token)
                    i += 2
                    pred_tokens = []
                    n_paranthesis = 1  
                    while i < len(tokens):
                        if tokens[i] == '(':
                            n_paranthesis += 1
                        if tokens[i] == ')':
                            n_paranthesis -= 1         
                        if n_paranthesis == 0:
                            pred.set_terms(pred_tokens)   
                            break
                        else:
                            pred_tokens.append(tokens[i])
                        i += 1
                    result.append(pred)
                else:
                    result.append(token)
            i += 1
        return result

    @staticmethod
    def infixToPostfix(infix):
        if len(infix) == 1:
            return infix
        infix = ["("] + infix + [")"]
        l = len(infix)        op_stack = []
        output = []
        
        i = 0
        while i < len(infix):
            if infix[i] == "(":
                op_stack.append(infix[i])
            elif infix[i] == ")":
                while op_stack[-1] != "(":
                    operator = op_stack.pop()
                    if operator.quantifier:
                        bound_variables.remove(operator.quanified_variable)
                    output.append(operator)
                op_stack.pop()

            elif isOperator(infix[i]):
                while op_stack[-1] != '(' and infix[i].getPriority() <= op_stack[-1].getPriority():
                    operator = op_stack.pop()
                    if operator.quantifier:
                        bound_variables.remove(operator.quanified_variable)
                    output.append(operator)

                if infix[i].quantifier:
                    op, variable = str(infix[i]).split(" ")
                    op_stack.append(Operator(op + " ((" + variable + " BoundSet" + "))"))
                    bound_variables.add(variable)
                else:
                    op_stack.append(infix[i])

            else:
                output.append(infix[i])
            i += 1
        
        while len(op_stack) != 0:
            operator = op_stack.pop()
            if operator != '(' and operator.quantifier:
                bound_variables.remove(operator.quanified_variable)
            output.append(operator)
        
        return output            

    @staticmethod
    def generatePrefixFormula(tokens):
        infix = tokens[::-1]  
        for i in range(len(infix)):
            if infix[i] == "(":
                infix[i] = ")"
            elif infix[i] == ")":
                infix[i] = "("
        reverse_postfix = CVCGenerator.infixToPostfix(infix)
        stack = []
        for token in reverse_postfix:
            if not isOperator(token):
                stack.append(token)
            else:
                arity = Operator.getOperatorArity(token)
                if arity == 1:
                    operand = stack.pop()
                    parenthesized_expr = "("+ str(token) + " " + str(operand) +")"
                else: 
                    operand1 = stack.pop()
                    operand2 = stack.pop()
                    parenthesized_expr = "(" + str(token) + " " + str(operand1) + " " + str(operand2) + ")"
                stack.append(parenthesized_expr)
        
        return stack[0]

    def generateCVCScript(self, finite_model_finding=False):
        cvc_str = "(set-logic ALL)\n(set-option :produce-models true)\n(declare-sort BoundSet 0)\n(declare-sort UnboundSet 0)"
        if finite_model_finding:
            cvc_str += ("\n(set-option :finite-model-find true)")   
                        
        prefix_formula = CVCGenerator.generatePrefixFormula(self.tokens)
        
        for variable in unbound_variables:
            if not unbound_variables[variable].getSort():
                unbound_variables[variable].setSort("UnboundSet")
            cvc_str += "\n(declare-fun {0} () {1})".format(variable, unbound_variables[variable])

        for predicate in predicate_to_sort_map:
            sort = " ".join([str(s) for s in predicate_to_sort_map[predicate]])
            cvc_str += "\n(declare-fun {0} ({1}) Bool)".format(predicate, sort)

        cvc_str += "\n(assert (not {0}))".format(prefix_formula)

        cvc_str += "\n(check-sat)\n(get-model)"
        return cvc_str

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python cvc.py "<fol>"')
        sys.exit(1)

    script = CVCGenerator(sys.argv[1].replace("ForAll", "forall").replace("ThereExists", "exists").replace("&", "and").replace("~", "not ")).generateCVCScript()
    print(script)