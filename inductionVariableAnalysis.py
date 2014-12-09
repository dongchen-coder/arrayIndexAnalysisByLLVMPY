from llvm import *
from llvm.core import *

from os.path import dirname, join as join_path

#load the file which is going to be analysised
asmfile = join_path(dirname(__file__), 'matrixMul.ll')
with open(asmfile) as asm:
    mod = Module.from_assembly(asm)

inductionVariables = ["a","b"]
tmpResult = []
for f in mod.functions:
    if f.name == "matrixMulCUDA":
        for elm in inductionVariables:
            iVinstructions = []
            for bb in f.basic_blocks:
                for istr in bb.instructions:
                    if istr.opcode == OPCODE_STORE:
                        if istr.operands[1].name == elm:
                            iVinstructions.append(istr.operands[0])

            for istr in iVinstructions:
                stack = []
                stack.append(istr)
                
                stackptr = 0;
                stacklen = 1;
                while stackptr<stacklen:
                    if isinstance(stack[stackptr],Instruction) == False:
                        stackptr=stackptr+1
                        continue
                    if stack[stackptr].opcode == OPCODE_LOAD:
                        #print stack[stackptr].operands[0].name
                        if not stack[stackptr].operands[0].name in inductionVariables:
                            if not stack[stackptr].operands[0].name == '':
                                inductionVariables.append(stack[stackptr].operands[0].name)
                        stackptr=stackptr+1
                        continue
                    if stack[stackptr].operand_count==1:
                        stack.append(stack[stackptr].operands[0])
                        stacklen=stacklen+1
                    if stack[stackptr].operand_count==2:
                        stack.append(stack[stackptr].operands[0])
                        stack.append(stack[stackptr].operands[1])
                        stacklen=stacklen+2
                    if stack[stackptr].operand_count==3:
                        stack.append(stack[stackptr].operands[0])
                        stack.append(stack[stackptr].operands[1])
                        stack.append(stack[stackptr].operands[2])
                        stacklen=stacklen+3
                    stackptr=stackptr+1

                namestack = []
                for selm in stack:
                    if isinstance(selm,Instruction):
                        if selm.opcode == OPCODE_LOAD:
                            #load a varaible
                            if not selm.operands[0].name=='':
                                namestack.append(selm.operands[0].name)
                            #load an argument
                            elif selm.operands[0].opcode == OPCODE_GETELEMENTPTR:
                                if (selm.operands[0].operands[2].z_ext_value == 0):
                                    namestack.append(selm.operands[0].operands[0].name+".x")
                                if (selm.operands[0].operands[2].z_ext_value == 1):
                                    namestack.append(selm.operands[0].operands[0].name+".y")
                                if (selm.operands[0].operands[2].z_ext_value == 2):
                                    namestack.append(selm.operands[0].operands[0].name+".z")
                            else:
                                strStart = str(selm.operands[0]).find('%')
                                strEnd = str(selm.operands[0]).find('=')
                                argNum = str(selm.operands[0])[strStart+1:strEnd]
                                namestack.append(f.args[int(argNum)-1].name)
                        elif selm.opcode == OPCODE_ICMP:
                            if selm.predicate == 40:
                                if flag == "true":
                                    namestack.append(' < ')
                                if flag == "false":
                                    namestack.append(' >= ')
                            elif selm.predicate == 41:
                                if flag == "true":
                                    namestack.append(' <= ')
                                if flag == "false":
                                    namestack.append(' > ')
                            else:
                                namestack.append(selm.predicate)
                        else:
                            namestack.append(selm.opcode_name)
                    elif isinstance(selm,ConstantInt):
                        namestack.append(selm.z_ext_value)

                for index_j in range(0,stacklen):
                    if isinstance(namestack[index_j], (int, long, float, complex)):
                        namestack[index_j] = str(namestack[index_j])

                tail = stacklen-1
                for index in range(0,stacklen):
                    if namestack[stacklen-1-index] == 'mul':
                        namestack[stacklen-1-index] = namestack[tail-1] + ' * ' + namestack[tail]
                        tail=tail-2
                    if namestack[stacklen-1-index] == 'add':
                        namestack[stacklen-1-index] = namestack[tail-1] + ' + ' + namestack[tail]
                        tail=tail-2
                    if namestack[stacklen-1-index] == 'sext':
                        namestack[stacklen-1-index] = namestack[tail]
                        tail=tail-1
                    if namestack[stacklen-1-index] == ' < ':
                        namestack[stacklen-1-index] = namestack[tail-1] + ' < ' + namestack[tail]
                        tail=tail-2
                    if namestack[stacklen-1-index] == ' <= ':
                        namestack[stacklen-1-index] = namestack[tail-1] + ' <= ' + namestack[tail]
                        tail=tail-2
                    if namestack[stacklen-1-index] == ' > ':
                        namestack[stacklen-1-index] = namestack[tail-1] + ' > ' + namestack[tail]
                        tail=tail-2
                    if namestack[stacklen-1-index] == ' >= ':
                        namestack[stacklen-1-index] = namestack[tail-1] + ' >= ' + namestack[tail]
                        tail=tail-2
            
                tmpResult.append(elm + " = " + str(namestack[0]))

for index_i in range(0,4):
    #print tmpResult[index_i]
    for index_j in range(4,len(tmpResult)):
        end = tmpResult[index_j].find(" = ")
        #print tmpResult[index_i].find(tmpResult[index_j][0:end])
        tmpResult[index_i] = tmpResult[index_i].replace(tmpResult[index_j][0:end],tmpResult[index_j][end+3:len(tmpResult[index_j])])

print "induction variables analysis result======"
for index_i in range(0,4):
    print tmpResult[index_i]


