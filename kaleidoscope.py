#!/usr/bin/env python

import re
from llvm.core import Module, Constant, Type, Function, Builder
from llvm.ee import ExecutionEngine, TargetData
from llvm.passes import FunctionPassManager

from llvm.core import FCMP_ULT, FCMP_ONE
from llvm.passes import(
                        #PASS_PROMOTE_MEMORY_TO_REGISTER,
                        #PASS_INSTRUCTION_COMBINING,
                        PASS_REASSOCIATE,
                        PASS_GVN,
                        #PASS_CFG_SIMPLIFICATION
                        )

# The LLVM module, which holds all the IR code.
g_llvm_module = Module.new('my cool jit')

# The LLVM instruction builder. Created whenever a new function is entered.
g_llvm_builder = None

# A dictionary that keeps track of which values are defined in the current scope
# and what their LLVM representation is.
g_named_values = {}

# The function optimization passes manager.
g_llvm_pass_manager = FunctionPassManager.new(g_llvm_module)

# The LLVM execution engine.
g_llvm_executor = ExecutionEngine.new(g_llvm_module)

# The binary operator precedence chart.
g_binop_precedence = {}

# Creates an alloca instruction in the entry block of the function. This is used
# for mutable variables.
def CreateEntryBlockAlloca(function, var_name):
    entry = function.get_entry_basic_block()
    builder = Builder.new(entry)
    builder.position_at_beginning(entry)
    return builder.alloca(Type.double(), None ,var_name) #dong chen

# The lexer yields one of these types for each token.
class EOFToken(object):
    pass
class DefToken(object):
    pass
class ExternToken(object):
    pass
class IfToken(object):
    pass
class ThenToken(object):
    pass
class ElseToken(object):
    pass
class ForToken(object):
    pass
class InToken(object):
    pass
class BinaryToken(object):
    pass
class UnaryToken(object):
    pass
class VarToken(object):
    pass

class IdentifierToken(object):
    def __init__(self, name):
        self.name = name

class NumberToken(object):
    def __init__(self, value):
        self.value = value

class CharacterToken(object):
    def __init__(self, char):
        self.char = char
    def __eq__(self, other):
        return isinstance(other, CharacterToken) and self.char == other.char
    def __ne__(self, other):
        return not self == other

# Regular expressions that tokens and comments of our language.
REGEX_NUMBER = re.compile('[0-9]+(?:\.[0-9]+)?')
REGEX_IDENTIFIER = re.compile('[a-zA-Z][a-zA-Z0-9]*')
REGEX_COMMENT = re.compile('#.*')

def Tokenize(string):
    while string:
        # Skip whitespace.
        if string[0].isspace():
            string = string[1:]
            continue
                    
        # Run regexes.
        comment_match = REGEX_COMMENT.match(string)
        number_match = REGEX_NUMBER.match(string)
        identifier_match = REGEX_IDENTIFIER.match(string)
                                
        # Check if any of the regexes matched and yield the appropriate result.
        if comment_match:
            comment = comment_match.group(0)
            string = string[len(comment):]
        elif number_match:
            number = number_match.group(0)
            yield NumberToken(float(number))
            string = string[len(number):]
        elif identifier_match:
            identifier = identifier_match.group(0)
            # Check if we matched a keyword.
            if identifier == 'def':
                yield DefToken()
            elif identifier == 'extern':
                yield ExternToken()
            elif identifier == 'if':
                yield IfToken()
            elif identifier == 'then':
                yield ThenToken()
            elif identifier == 'else':
                yield ElseToken()
            elif identifier == 'for':
                yield ForToken()
            elif identifier == 'in':
                yield InToken()
            elif identifier == 'binary':
                yield BinaryToken()
            elif identifier == 'unary':
                yield UnaryToken()
            elif identifier == 'var':
                yield VarToken()
            else:
                yield IdentifierToken(identifier)
            string = string[len(identifier):]
        else:
            # Yield the ASCII value of the unknown character.
            yield CharacterToken(string[0])
            string = string[1:]
        
    yield EOFToken()

# Base class for all expression nodes.
class ExpressionNode(object):
    pass

# Expression class for numeric literals like "1.0".
class NumberExpressionNode(ExpressionNode):
    
    def __init__(self, value):
        self.value = value
            
    def CodeGen(self):
        return Constant.real(Type.double(), self.value)

# Expression class for referencing a variable, like "a".
class VariableExpressionNode(ExpressionNode):
    
    def __init__(self, name):
        self.name = name
            
    def CodeGen(self):
        if self.name in g_named_values:
            return g_llvm_builder.load(g_named_values[self.name], self.name)
        else:
            raise RuntimeError('Unknown variable name: ' + self.name)

# Expression class for a binary operator.
class BinaryOperatorExpressionNode(ExpressionNode):
    
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right
                    
    def CodeGen(self):
        # A special case for '=' because we don't want to emit the LHS as an # expression.
        if self.operator == '=':
            # Assignment requires the LHS to be an identifier.
            if not isinstance(self.left, VariableExpressionNode):
                raise RuntimeError('Destination of "=" must be a variable.')
                                    
            # Codegen the RHS.
            value = self.right.CodeGen()
                                        
            # Look up the name.
            variable = g_named_values[self.left.name]
                                            
            # Store the value and return it.
            g_llvm_builder.store(value, variable)
                                                
            return value
                                                    
        left = self.left.CodeGen()
        right = self.right.CodeGen()
                                                            
        if self.operator == '+':
            return g_llvm_builder.fadd(left, right, 'addtmp')
        elif self.operator == '-':
            return g_llvm_builder.fsub(left, right, 'subtmp')
        elif self.operator == '*':
            return g_llvm_builder.fmul(left, right, 'multmp')
        elif self.operator == '<':
            result = g_llvm_builder.fcmp(FCMP_ULT, left, right, 'cmptmp')
            # Convert bool 0 or 1 to double 0.0 or 1.0.
            return g_llvm_builder.uitofp(result, Type.double(), 'booltmp')
        else:
            function = g_llvm_module.get_function_named('binary' + self.operator)
            return g_llvm_builder.call(function, [left, right], 'binop')

# Expression class for function calls.
class CallExpressionNode(ExpressionNode):
    
    def __init__(self, callee, args):
        self.callee = callee
        self.args = args
                
    def CodeGen(self):
        # Look up the name in the global module table.
        callee = g_llvm_module.get_function_named(self.callee)
                        
        # Check for argument mismatch error.
        if len(callee.args) != len(self.args):
            raise RuntimeError('Incorrect number of arguments passed.')
                                
        arg_values = [i.CodeGen() for i in self.args]
                                    
        return g_llvm_builder.call(callee, arg_values, 'calltmp')

# Expression class for if/then/else.
class IfExpressionNode(ExpressionNode):
    
    def __init__(self, condition, then_branch, else_branch):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
                    
    def CodeGen(self):
        condition = self.condition.CodeGen()
                            
        # Convert condition to a bool by comparing equal to 0.0.
        condition_bool = g_llvm_builder.fcmp(FCMP_ONE, condition, Constant.real(Type.double(), 0), 'ifcond')
                                
        function = g_llvm_builder.basic_block.function
                                    
        # Create blocks for the then and else cases. Insert the 'then' block at the
        # end of the function.
        then_block = function.append_basic_block('then')
        else_block = function.append_basic_block('else')
        merge_block = function.append_basic_block('ifcond')
                                                
        g_llvm_builder.cbranch(condition_bool, then_block, else_block)
                                                    
        # Emit then value.
        g_llvm_builder.position_at_end(then_block)
        then_value = self.then_branch.CodeGen()
        g_llvm_builder.branch(merge_block)
                                                                
        # Codegen of 'Then' can change the current block; update then_block for the
        # PHI node.
        then_block = g_llvm_builder.basic_block
                                                                    
        # Emit else block.
        g_llvm_builder.position_at_end(else_block)
        else_value = self.else_branch.CodeGen()
        g_llvm_builder.branch(merge_block)
                                                                                
        # Codegen of 'Else' can change the current block, update else_block for the
        # PHI node.
        else_block = g_llvm_builder.basic_block
                                                                                    
        # Emit merge block.
        g_llvm_builder.position_at_end(merge_block)
        phi = g_llvm_builder.phi(Type.double(), 'iftmp')
        phi.add_incoming(then_value, then_block)
        phi.add_incoming(else_value, else_block)
                                                                                                    
        return phi

# Expression class for for/in.
class ForExpressionNode(ExpressionNode):
    
    def __init__(self, loop_variable, start, end, step, body):
        self.loop_variable = loop_variable
        self.start = start
        self.end = end
        self.step = step
        self.body = body
                            
    def CodeGen(self):
        # Output this as:
        #   var = alloca double
        #   ...
        #   start = startexpr
        #   store start -> var
        #   goto loop
        # loop:
        #   ...
        #   bodyexpr
        #   ...
        # loopend:
        #   step = stepexpr
        #   endcond = endexpr
        #
        #   curvar = load var
        #   nextvar = curvar + step
        #   store nextvar -> var
        #   br endcond, loop, endloop
        # outloop:
        
        function = g_llvm_builder.basic_block.function
                                    
        # Create an alloca for the variable in the entry block.
        alloca = CreateEntryBlockAlloca(function, self.loop_variable)
                                        
        # Emit the start code first, without 'variable' in scope.
        start_value = self.start.CodeGen()
                                            
        # Store the value into the alloca.
        g_llvm_builder.store(start_value, alloca)
                                                
        # Make the new basic block for the loop, inserting after current block.
        loop_block = function.append_basic_block('loop')
                                                    
        # Insert an explicit fall through from the current block to the loop_block.
        g_llvm_builder.branch(loop_block)
                                                        
        # Start insertion in loop_block.
        g_llvm_builder.position_at_end(loop_block)
                                                            
        # Within the loop, the variable is defined equal to the alloca.  If it
        # shadows an existing variable, we have to restore it, so save it now.
        old_value = g_named_values.get(self.loop_variable, None)
        g_named_values[self.loop_variable] = alloca
                                                                    
        # Emit the body of the loop.  This, like any other expr, can change the
        # current BB.  Note that we ignore the value computed by the body.
        self.body.CodeGen()
                                                                        
        # Emit the step value.
        if self.step:
            step_value = self.step.CodeGen()
        else:
            # If not specified, use 1.0.
            step_value = Constant.real(Type.double(), 1)
                                                                                        
        # Compute the end condition.
        end_condition = self.end.CodeGen()
                                                                                            
        # Reload, increment, and restore the alloca.  This handles the case where
        # the body of the loop mutates the variable.
        cur_value = g_llvm_builder.load(alloca, self.loop_variable)
        next_value = g_llvm_builder.fadd(cur_value, step_value, 'nextvar')
        g_llvm_builder.store(next_value, alloca)
                                                                                                        
        # Convert condition to a bool by comparing equal to 0.0.
        end_condition_bool = g_llvm_builder.fcmp(FCMP_ONE, end_condition, Constant.real(Type.double(), 0), 'loopcond')
                                                                                                            
        # Create the "after loop" block and insert it.
        after_block = function.append_basic_block('afterloop')
                                                                                                                
        # Insert the conditional branch into the end of loop_block.
        g_llvm_builder.cbranch(end_condition_bool, loop_block, after_block)
                                                                                                                    
        # Any new code will be inserted in after_block.
        g_llvm_builder.position_at_end(after_block)
                                                                                                                        
        # Restore the unshadowed variable.
        if old_value is not None:
            g_named_values[self.loop_variable] = old_value
        else:
            del g_named_values[self.loop_variable]
                                                                                                                                        
        # for expr always returns 0.0.
        return Constant.real(Type.double(), 0)

# Expression class for a unary operator.
class UnaryExpressionNode(ExpressionNode):
    
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand
                
    def CodeGen(self):
        operand = self.operand.CodeGen()
        function = g_llvm_module.get_function_named('unary' + self.operator)
        return g_llvm_builder.call(function, [operand], 'unop')

# Expression class for var/in.
class VarExpressionNode(ExpressionNode):
    
    def __init__(self, variables, body):
        self.variables = variables
        self.body = body
                
    def CodeGen(self):
        old_bindings = {}
        function = g_llvm_builder.basic_block.function
                            
        # Register all variables and emit their initializer.
        for var_name, var_expression in self.variables.iteritems():
        # Emit the initializer before adding the variable to scope, this prevents
        # the initializer from referencing the variable itself, and permits stuff
        # like this:
        #  var a = 1 in
        #    var a = a in ...   # refers to outer 'a'.
            if var_expression is not None:
                var_value = var_expression.CodeGen()
            else:
                var_value = Constant.real(Type.double(), 0)
                                                
            alloca = CreateEntryBlockAlloca(function, var_name)
            g_llvm_builder.store(var_value, alloca)
                                                        
            # Remember the old variable binding so that we can restore the binding
            # when we unrecurse.
            old_bindings[var_name] = g_named_values.get(var_name, None)
                                                            
            # Remember this binding.
            g_named_values[var_name] = alloca
                                                                
        # Codegen the body, now that all vars are in scope.
        body = self.body.CodeGen()
                                                                    
        # Pop all our variables from scope.
        for var_name in self.variables:
            if old_bindings[var_name] is not None:
                g_named_values[var_name] = old_bindings[var_name]
            else:
                del g_named_values[var_name]
                                                                                        
        # Return the body computation.
        return body

# This class represents the "prototype" for a function, which captures its name,
# and its argument names (thus implicitly the number of arguments the function
# takes), as well as if it is an operator.
class PrototypeNode(object):
    
    def __init__(self, name, args, is_operator=False, precedence=0):
        self.name = name
        self.args = args
        self.is_operator = is_operator
        self.precedence = precedence
                        
    def IsBinaryOp(self):
        return self.is_operator and len(self.args) == 2
                                
    def GetOperatorName(self):
        assert self.is_operator
        return self.name[-1]
                                            
    def CodeGen(self):
        # Make the function type, eg. double(double,double).
        funct_type = Type.function(Type.double(), [Type.double()] * len(self.args), False)
                                                    
        function = Function.new(g_llvm_module, funct_type, self.name)
                                                        
        # If the name conflicted, there was already something with the same name.
        # If it has a body, don't allow redefinition or reextern.
        if function.name != self.name:
            function.delete()
            function = g_llvm_module.get_function_named(self.name)
                                                                    
            # If the function already has a body, reject this.
            if not function.is_declaration:
                raise RuntimeError('Redefinition of function.')
                                                                            
            # If the function took a different number of args, reject.
            if len(function.args) != len(self.args):
                raise RuntimeError('Redeclaration of a function with different number of args.')
                                                                                    
        # Set names for all arguments and add them to the variables symbol table.
        for arg, arg_name in zip(function.args, self.args):
            arg.name = arg_name
                                                                                            
        return function
                                                                                                
        # Create an alloca for each argument and register the argument in the symbol
        # table so that references to it will succeed.
    def CreateArgumentAllocas(self, function):
        for arg_name, arg in zip(self.args, function.args):
            alloca = CreateEntryBlockAlloca(function, arg_name)
            g_llvm_builder.store(arg, alloca)
            g_named_values[arg_name] = alloca

# This class represents a function definition itself.
class FunctionNode(object):
    
    def __init__(self, prototype, body):
        self.prototype = prototype
        self.body = body
                
    def CodeGen(self):
        # Clear scope.
        g_named_values.clear()
                        
        # Create a function object.
        function = self.prototype.CodeGen()
                            
        # If this is a binary operator, install its precedence.
        if self.prototype.IsBinaryOp():
            operator = self.prototype.GetOperatorName()
            g_binop_precedence[operator] = self.prototype.precedence
                                        
        # Create a new basic block to start insertion into.
        block = function.append_basic_block('entry')
        global g_llvm_builder
        g_llvm_builder = Builder.new(block)
                                                    
        # Add all arguments to the symbol table and create their allocas.
        self.prototype.CreateArgumentAllocas(function)
                                                        
        # Finish off the function.
        try:
            return_value = self.body.CodeGen()
            g_llvm_builder.ret(return_value)
                                                                    
            # Validate the generated code, checking for consistency.
            function.verify()
                                                                        
            # Optimize the function.
            g_llvm_pass_manager.run(function)
        except:
            function.delete()
            if self.prototype.IsBinaryOp():
                del g_binop_precedence[self.prototype.GetOperatorName()]
            raise
                                                                                                
        return function


class Parser(object):
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.Next()
                
    # Provide a simple token buffer. Parser.current is the current token the
    # parser is looking at. Parser.Next() reads another token from the lexer and
    # updates Parser.current with its results.
    def Next(self):
        self.current = self.tokens.next()
                        
    # Gets the precedence of the current token, or -1 if the token is not a binary
    # operator.
    def GetCurrentTokenPrecedence(self):
        if isinstance(self.current, CharacterToken):
            return g_binop_precedence.get(self.current.char, -1)
        else:
            return -1
                                            
    # identifierexpr ::= identifier | identifier '(' expression* ')'
    def ParseIdentifierExpr(self):
        identifier_name = self.current.name
        self.Next()  # eat identifier.
                                                        
        if self.current != CharacterToken('('):  # Simple variable reference.
            return VariableExpressionNode(identifier_name)
                                                                
        # Call.
        self.Next()  # eat '('.
        args = []
        if self.current != CharacterToken(')'):
            while True:
                args.append(self.ParseExpression())
                if self.current == CharacterToken(')'):
                    break
                elif self.current != CharacterToken(','):
                    raise RuntimeError('Expected ")" or "," in argument list.')
                self.Next()
                                                                                                        
        self.Next()  # eat ')'.
        return CallExpressionNode(identifier_name, args)

    # numberexpr ::= number
    def ParseNumberExpr(self):
        result = NumberExpressionNode(self.current.value)
        self.Next()  # consume the number.
        return result
                
    # parenexpr ::= '(' expression ')'
    def ParseParenExpr(self):
        self.Next()  # eat '('.
                        
        contents = self.ParseExpression()
                            
        if self.current != CharacterToken(')'):
            raise RuntimeError('Expected ")".')
        self.Next()  # eat ')'.
                                        
        return contents
                                            
    # ifexpr ::= 'if' expression 'then' expression 'else' expression
    def ParseIfExpr(self):
        self.Next()  # eat the if.
                                                    
        # condition.
        condition = self.ParseExpression()
                                                        
        if not isinstance(self.current, ThenToken):
            raise RuntimeError('Expected "then".')
        self.Next()  # eat the then.
                                                                    
        then_branch = self.ParseExpression()
                                                                        
        if not isinstance(self.current, ElseToken):
            raise RuntimeError('Expected "else".')
        self.Next()  # eat the else.
                                                                                    
        else_branch = self.ParseExpression()
                                                                                        
        return IfExpressionNode(condition, then_branch, else_branch)
                                                                                            
    # forexpr ::= 'for' identifier '=' expr ',' expr (',' expr)? 'in' expression
    def ParseForExpr(self):
        self.Next()  # eat the for.
                                                                                                    
        if not isinstance(self.current, IdentifierToken):
            raise RuntimeError('Expected identifier after for.')
                                                                                                            
        loop_variable = self.current.name
        self.Next()  # eat the identifier.
                                                                                                                    
        if self.current != CharacterToken('='):
            raise RuntimeError('Expected "=" after for variable.')
        self.Next()  # eat the '='.
                                                                                                                                
        start = self.ParseExpression()
                                                                                                                                    
        if self.current != CharacterToken(','):
            raise RuntimeError('Expected "," after for start value.')
        self.Next()  # eat the ','.
                                                                                                                                                
        end = self.ParseExpression()
                                                                                                                                                    
        # The step value is optional.
        if self.current == CharacterToken(','):
            self.Next()  # eat the ','.
            step = self.ParseExpression()
        else:
            step = None
                                                                                                                                                                        
        if not isinstance(self.current, InToken):
            raise RuntimeError('Expected "in" after for variable specification.')
        self.Next()  # eat 'in'.
                                                                                                                                                                                    
        body = self.ParseExpression()
                                                                                                                                                                                        
        return ForExpressionNode(loop_variable, start, end, step, body)
                                                                                                                                                                                            
   # varexpr ::= 'var' (identifier ('=' expression)?)+ 'in' expression
    def ParseVarExpr(self):
        self.Next()  # eat 'var'.

        variables = {}
                                                                                                                                                                                                        
        # At least one variable name is required.
        if not isinstance(self.current, IdentifierToken):
            raise RuntimeError('Expected identifier after "var".')
                                                                                                                                                                                                                
        while True:
            var_name = self.current.name
            self.Next()  # eat the identifier.
                                                                                                                                                                                                                            
            # Read the optional initializer.
            if self.current == CharacterToken('='):
                self.Next()  # eat '='.
                variables[var_name] = self.ParseExpression()
            else:
                variables[var_name] = None
                                                                                                                                                                                                                                                
            # End of var list, exit loop.
            if self.current != CharacterToken(','):
                break
            self.Next()  # eat ','.
                                                                                                                                                                                                                                                            
            if not isinstance(self.current, IdentifierToken):
                raise RuntimeError('Expected identifier after "," in a var expression.')
                                                                                                                                                                                                                                                                    
        # At this point, we have to have 'in'.
        if not isinstance(self.current, InToken):
            raise RuntimeError('Expected "in" keyword after "var".')
        self.Next()  # eat 'in'.
                                                                                                                                                                                                                                                                                
        body = self.ParseExpression()
                                                                                                                                                                                                                                                                                    
        return VarExpressionNode(variables, body)
                                                                                                                                                                                                                                                                                        
    # primary ::=
    # dentifierexpr | numberexpr | parenexpr | ifexpr | forexpr | varexpr
    def ParsePrimary(self):
        if isinstance(self.current, IdentifierToken):
            return self.ParseIdentifierExpr()
        elif isinstance(self.current, NumberToken):
            return self.ParseNumberExpr()
        elif isinstance(self.current, IfToken):
            return self.ParseIfExpr()
        elif isinstance(self.current, ForToken):
            return self.ParseForExpr()
        elif isinstance(self.current, VarToken):
            return self.ParseVarExpr()
        elif self.current == CharacterToken('('):
            return self.ParseParenExpr()
        else:
            raise RuntimeError('Unknown token when expecting an expression.')


    # unary ::= primary | unary_operator unary
    def ParseUnary(self):
        # If the current token is not an operator, it must be a primary expression.
        if (not isinstance(self.current, CharacterToken) or self.current in [CharacterToken('('), CharacterToken(',')]):
            return self.ParsePrimary()
            
        # If this is a unary operator, read it.
        operator = self.current.char
        self.Next()  # eat the operator.
        return UnaryExpressionNode(operator, self.ParseUnary())
                        
    # binoprhs ::= (binary_operator unary)*
    def ParseBinOpRHS(self, left, left_precedence):
        # If this is a binary operator, find its precedence.
        while True:
            precedence = self.GetCurrentTokenPrecedence()
                                    
            # If this is a binary operator that binds at least as tightly as the
            # current one, consume it; otherwise we are done.
            if precedence < left_precedence:
                return left
                                            
            binary_operator = self.current.char
            self.Next()  # eat the operator.
                                                    
            # Parse the unary expression after the binary operator.
            right = self.ParseUnary()
                                                        
            # If binary_operator binds less tightly with right than the operator after
            # right, let the pending operator take right as its left.
            next_precedence = self.GetCurrentTokenPrecedence()
            if precedence < next_precedence:
                right = self.ParseBinOpRHS(right, precedence + 1)
                                                                    
            # Merge left/right.
            left = BinaryOperatorExpressionNode(binary_operator, left, right)
                                                                        
    # expression ::= unary binoprhs
    def ParseExpression(self):
        left = self.ParseUnary()
        return self.ParseBinOpRHS(left, 0)
                                                                                    
    # prototype
    #   ::= id '(' id* ')'
    #   ::= binary LETTER number? (id, id)
    #   ::= unary LETTER (id)
    def ParsePrototype(self):
        precedence = None
        if isinstance(self.current, IdentifierToken):
            kind = 'normal'
            function_name = self.current.name
            self.Next() #  eat function name.
        elif isinstance(self.current, UnaryToken):
            kind = 'unary'
            self.Next() #  eat 'unary'.
            if not isinstance(self.current, CharacterToken):
                raise RuntimeError('Expected an operator after "unary".')
            function_name = 'unary' + self.current.char
            self.Next() # eat the operator.
        elif isinstance(self.current, BinaryToken):
            kind = 'binary'
            self.Next() #  eat 'binary'.
            if not isinstance(self.current, CharacterToken):
                raise RuntimeError('Expected an operator after "binary".')
            function_name = 'binary' + self.current.char
            self.Next() # eat the operator.
            if isinstance(self.current, NumberToken):
                if not 1 <= self.current.value <= 100:
                    raise RuntimeError('Invalid precedence: must be in range [1, 100].')
                precedence = self.current.value
                self.Next()  # eat the precedence.
        else:
            raise RuntimeError('Expected function name, "unary" or "binary" in prototype.')
                                                                                                                                                                                                
        if self.current != CharacterToken('('):
            raise RuntimeError('Expected "(" in prototype.')
        self.Next()  # eat '('.
                                                                                                                                                                                                            
        arg_names = []
        while isinstance(self.current, IdentifierToken):
            arg_names.append(self.current.name)
            self.Next()
                                                                                                                                                                                                                            
        if self.current != CharacterToken(')'):
            raise RuntimeError('Expected ")" in prototype.')
                                                                                                                                                                                                                                    
        # Success.
        self.Next()  # eat ')'.
                                                                                                                                                                                                                                        
        if kind == 'unary' and len(arg_names) != 1:
            raise RuntimeError('Invalid number of arguments for a unary operator.')
        elif kind == 'binary' and len(arg_names) != 2:
            raise RuntimeError('Invalid number of arguments for a binary operator.')

        return PrototypeNode(function_name, arg_names, kind != 'normal', precedence)
                                                                                                                                                                                                                                                            
    # definition ::= 'def' prototype expression
    def ParseDefinition(self):
        self.Next()  # eat def.
        proto = self.ParsePrototype()
        body = self.ParseExpression()
        return FunctionNode(proto, body)
                                                                                                                                                                                                                                                                                
    # toplevelexpr ::= expression
    def ParseTopLevelExpr(self):
        proto = PrototypeNode('', [])
        return FunctionNode(proto, self.ParseExpression())
                                                                                                                                                                                                                                                                                            
    # external ::= 'extern' prototype
    def ParseExtern(self):
        self.Next()  # eat extern.
        return self.ParsePrototype()
    
    # Top-Level parsing
    def HandleDefinition(self):
        self.Handle(self.ParseDefinition, 'Read a function definition:')
                                                                                                                                                                                                                                                                                                                
    def HandleExtern(self):
        self.Handle(self.ParseExtern, 'Read an extern:')
                                                                                                                                                                                                                                                                                                                        
    def HandleTopLevelExpression(self):
        try:
            function = self.ParseTopLevelExpr().CodeGen()
            result = g_llvm_executor.run_function(function, [])
            print 'Evaluated to:', result.as_real(Type.double())
        except Exception, e:
            raise#print 'Error:', e
            try:
                self.Next()  # Skip for error recovery.
            except:
                pass

    def Handle(self, function, message):
        try:
            print message, function().CodeGen()
        except Exception, e:
            raise#print 'Error:', e
            try:
                self.Next()  # Skip for error recovery.
            except:
                pass


def main():
    # Set up the optimizer pipeline. Start with registering info about how the
    # target lays out data structures.
    g_llvm_pass_manager.add(g_llvm_executor.target_data)
    # Promote allocas to registers.
    #    g_llvm_pass_manager.add(PASS_PROMOTE_MEMORY_TO_REGISTER)
    # Do simple "peephole" optimizations and bit-twiddling optzns.
    #    g_llvm_pass_manager.add(PASS_INSTRUCTION_COMBINING)
    # Reassociate expressions.
    g_llvm_pass_manager.add(PASS_REASSOCIATE)
    # Eliminate Common SubExpressions.
    g_llvm_pass_manager.add(PASS_GVN)
    # Simplify the control flow graph (deleting unreachable blocks, etc).
    #    g_llvm_pass_manager.add(PASS_CFG_SIMPLIFICATION)
                            
    g_llvm_pass_manager.initialize()
                                
    # Install standard binary operators.
    # 1 is lowest possible precedence. 40 is the highest.
    g_binop_precedence['='] = 2
    g_binop_precedence['<'] = 10
    g_binop_precedence['+'] = 20
    g_binop_precedence['-'] = 20
    g_binop_precedence['*'] = 40
                                                    
    # Run the main "interpreter loop".
    while True:
        print 'ready<',
        try:
            raw = raw_input()
        except KeyboardInterrupt:
            break
                                                                            
        parser = Parser(Tokenize(raw))
        while True:
            # top ::= definition | external | expression | EOF
            if isinstance(parser.current, EOFToken):
                break
            if isinstance(parser.current, DefToken):
                parser.HandleDefinition()
            elif isinstance(parser.current, ExternToken):
                parser.HandleExtern()
            else:
                parser.HandleTopLevelExpression()
                                                                                                                    
    # Print out all of the generated code.
    print '', g_llvm_module

if __name__ ==  '__main__':
    main()
