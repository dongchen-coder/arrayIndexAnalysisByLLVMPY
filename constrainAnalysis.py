from llvm import *
from llvm.core import *

from os.path import dirname, join as join_path


print "constrains analysis result==============="
#load the file which is going to be analysised
asmfile = join_path(dirname(__file__), 'matrixMul.ll')
with open(asmfile) as asm:
    mod = Module.from_assembly(asm)

#store basic block and its pre into bbPre[]
bbNum = 0
bbPre = []
for f in mod.functions:
    if f.name == "matrixMulCUDA":
        for bb in f.basic_blocks:
            bb.name = str(bbNum)
            bbPre.append([int(bb.name),[]])
            bbNum=bbNum+1

for f in mod.functions:
    for bb in f.basic_blocks:
        for scbb in bb.successors:
            bbPre[int(scbb.name)][1].append(int(bb.name))


#construct execution path tree and store it in ept
ept = []
for i in range(0,bbNum):
    tmpEpt = []
    tmpEpt.append([i])
    index = 0
    tmpEptLen = 1
    tmpResult = []
    while index < tmpEptLen:
        if not len(bbPre[tmpEpt[index][-1]][1]) == 0:
            for elm in bbPre[tmpEpt[index][-1]][1]:
                if not (elm in tmpEpt[index]): # if not (elm == 0 or (elm in tmpEpt[index])):
                    tmp = list(tmpEpt[index])
                    tmp.append(elm)
                    tmpEpt.append(tmp)
                    tmpEptLen = tmpEptLen + 1
                else:
                    tmpEpt[index].append(elm)
                    tmp = list(tmpEpt[index])
                    tmpResult.append(tmp)
        else:
            tmp = list(tmpEpt[index])
            tmpResult.append(tmp)
        index = index + 1
    ept.append(tmpResult)

# find the path which contain the entry block 0, which is the target path we want to extract constrains
print "full execution path:"
for elm in ept:
    print "Start From Basic Block " + str(ept.index(elm)) + " : " + str(elm)
    index = 0
    while index < len(elm):
        if not 0 in elm[index]:
            del elm[index]
        else:
            index = index + 1

print "execution path of a,b:" + str(ept[2][0])
result = []
# a,b is in block 2, c is in block 8
for f in mod.functions:
    if f.name == "matrixMulCUDA":
        for bb in f.basic_blocks:
            for path in ept[2]:
                for index in range(1,len(path)):
                    bbNumber = path[index]
                    if bb.name == str(bbNumber):
                        if bb.instructions[len(bb.instructions)-1].operand_count > 1:
                            flag = ""
                            if bb.instructions[len(bb.instructions)-1].operands[2].name == str(path[index-1]):
                                flag = "true"
                            if bb.instructions[len(bb.instructions)-1].operands[1].name == str(path[index-1]):
                                flag = "false"


                            stack = []
                            stack.append(bb.instructions[len(bb.instructions)-1].operands[0])
        
                            stackptr = 0;
                            stacklen = 1;
                            while stackptr<stacklen:
                                if isinstance(stack[stackptr],Instruction) == False:
                                    stackptr=stackptr+1
                                    continue
                                if stack[stackptr].opcode == OPCODE_LOAD:
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
                            for elm in stack:
                                if isinstance(elm,Instruction):
                                    if elm.opcode == OPCODE_LOAD:
                                        #load a varaible
                                        if not elm.operands[0].name=='':
                                            namestack.append(elm.operands[0].name)
                                        #load an argument
                                        else:
                                            strStart = str(elm.operands[0]).find('%')
                                            strEnd = str(elm.operands[0]).find('=')
                                            argNum = str(elm.operands[0])[strStart+1:strEnd]
                                            namestack.append(f.args[int(argNum)-1].name)
                                    elif elm.opcode == OPCODE_ICMP:
                                        if elm.predicate == 40:
                                            if flag == "true":
                                                namestack.append(' < ')
                                            if flag == "false":
                                                namestack.append(' >= ')
                                        elif elm.predicate == 41:
                                            if flag == "true":
                                                namestack.append(' <= ')
                                            if flag == "false":
                                                namestack.append(' > ')
                                        else:
                                            namestack.append(elm.predicate)
                                    else:
                                        namestack.append(elm.opcode_name)
                                elif isinstance(elm,ConstantInt):
                                    namestack.append(elm.z_ext_value)
                                        
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

                            result.append("a,b constrains: " + namestack[0])


print "execution path of c:" + str(ept[8][0])
# a,b is in block 2, c is in block 8
for f in mod.functions:
    if f.name == "matrixMulCUDA":
        for bb in f.basic_blocks:
            for path in ept[8]:
                for index in range(1,len(path)):
                    bbNumber = path[index]
                    if bb.name == str(bbNumber):
                        if bb.instructions[len(bb.instructions)-1].operand_count > 1:
                            flag = ""
                            if bb.instructions[len(bb.instructions)-1].operands[2].name == str(path[index-1]):
                                flag = "true"
                            if bb.instructions[len(bb.instructions)-1].operands[1].name == str(path[index-1]):
                                flag = "false"
                        
                            stack = []
                            stack.append(bb.instructions[len(bb.instructions)-1].operands[0])
                            
                            stackptr = 0;
                            stacklen = 1;
                            while stackptr<stacklen:
                                if isinstance(stack[stackptr],Instruction) == False:
                                    stackptr=stackptr+1
                                    continue
                                if stack[stackptr].opcode == OPCODE_LOAD:
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
                            for elm in stack:
                                if isinstance(elm,Instruction):
                                    if elm.opcode == OPCODE_LOAD:
                                        #load a varaible
                                        if not elm.operands[0].name=='':
                                            namestack.append(elm.operands[0].name)
                                        #load an argument
                                        else:
                                            strStart = str(elm.operands[0]).find('%')
                                            strEnd = str(elm.operands[0]).find('=')
                                            argNum = str(elm.operands[0])[strStart+1:strEnd]
                                            namestack.append(f.args[int(argNum)-1].name)
                                    elif elm.opcode == OPCODE_ICMP:
                                        if elm.predicate == 40:
                                            if flag == "true":
                                                namestack.append(' < ')
                                            if flag == "false":
                                                namestack.append(' >= ')
                                        elif elm.predicate == 41:
                                            if flag == "true":
                                                namestack.append(' <= ')
                                            if flag == "false":
                                                namestack.append(' > ')
                                        else:
                                            namestack.append(elm.predicate)
                                    else:
                                        namestack.append(elm.opcode_name)
                                elif isinstance(elm,ConstantInt):
                                    namestack.append(elm.z_ext_value)
                                        
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
                                                                                                                                        
                            result.append(" c constrains: " + namestack[0])


inductionVariables = ["aEnd"]
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
        #print inductionVariables
        #   print iVinstructions[0]
            for istr in iVinstructions:
                stack = []
                stack.append(istr)
                
                stackptr = 0;
                stacklen = 1;
                while stackptr<stacklen:
                    #print "=====" + str(stackptr)
                    #for test in stack:
                    #   print test
                    #print inductionVariables
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
                
                #print stacklen #debug only
                #for test in stack:
                #    print test
                
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
                                namestack.append(f.args[int(argNum)].name)
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
                    if namestack[stacklen-1-index] == 'sub':
                        namestack[stacklen-1-index] = namestack[tail-1] + ' - ' + namestack[tail]
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

    #print tmpResult[index_i]
for index_j in range(1,len(tmpResult)):
    end = tmpResult[index_j].find(" = ")
    #print tmpResult[index_i].find(tmpResult[index_j][0:end])
    tmpResult[0] = tmpResult[0].replace(tmpResult[index_j][0:end],tmpResult[index_j][end+3:len(tmpResult[index_j])])

for index_i in range(0,len(result)):
    end = tmpResult[0].find(" = ")
    result[index_i] = result[index_i].replace(tmpResult[0][0:end],tmpResult[0][end+3:len(tmpResult[0])])

#print tmpResult
for elm in result:
    print elm

'''
    OPCODE_RET            = 1
    OPCODE_BR             = 2
    OPCODE_SWITCH         = 3
    OPCODE_INDIRECT_BR    = 4
    OPCODE_INVOKE         = 5
    OPCODE_RESUME         = 6
    OPCODE_UNREACHABLE    = 7
    OPCODE_ADD            = 8
    OPCODE_FADD           = 9
    OPCODE_SUB            = 10
    OPCODE_FSUB           = 11
    OPCODE_MUL            = 12
    OPCODE_FMUL           = 13
    OPCODE_UDIV           = 14
    OPCODE_SDIV           = 15
    OPCODE_FDIV           = 16
    OPCODE_UREM           = 17
    OPCODE_SREM           = 18
    OPCODE_FREM           = 19
    OPCODE_SHL            = 20
    OPCODE_LSHR           = 21
    OPCODE_ASHR           = 22
    OPCODE_AND            = 23
    OPCODE_OR             = 24
    OPCODE_XOR            = 25
    OPCODE_ALLOCA         = 26
    OPCODE_LOAD           = 27
    OPCODE_STORE          = 28
    OPCODE_GETELEMENTPTR  = 29
    OPCODE_FENCE          = 30
    OPCODE_ATOMICCMPXCHG  = 31
    OPCODE_ATOMICRMW      = 32
    OPCODE_TRUNC          = 33
    OPCODE_ZEXT           = 34
    OPCODE_SEXT           = 35
    OPCODE_FPTOUI         = 36
    OPCODE_FPTOSI         = 37
    OPCODE_UITOFP         = 38
    OPCODE_SITOFP         = 39
    OPCODE_FPTRUNC        = 40
    OPCODE_FPEXT          = 41
    OPCODE_PTRTOINT       = 42
    OPCODE_INTTOPTR       = 43
    OPCODE_BITCAST        = 44
    OPCODE_ICMP           = 45
    OPCODE_FCMP           = 46
    OPCODE_PHI            = 47
    OPCODE_CALL           = 48
    OPCODE_SELECT         = 49
    OPCODE_USEROP1        = 50
    OPCODE_USEROP2        = 51
    OPCODE_VAARG          = 52
    OPCODE_EXTRACTELEMENT = 53
    OPCODE_INSERTELEMENT  = 54
    OPCODE_SHUFFLEVECTOR  = 55
    OPCODE_EXTRACTVALUE   = 56
    OPCODE_INSERTVALUE    = 57
    OPCODE_LANDINGPAD     = 58
    '''

