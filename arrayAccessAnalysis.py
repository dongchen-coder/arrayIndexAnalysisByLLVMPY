from llvm import *
from llvm.core import *

from os.path import dirname, join as join_path

#load the file which is going to be analysised
asmfile = join_path(dirname(__file__), 'matrixMul.ll')
with open(asmfile) as asm:
    mod = Module.from_assembly(asm)

#store the getelementptr instructions
getElementInsts = []
resultEquations = []

#store the getelemnetptr for constrain analysis
getElementInstsCandidate = []

#get all the getelementptr instructions in the list
for f in mod.functions:
    #print f
    for bb in f.basic_blocks:
        for istr in bb.instructions:
            if istr.opcode == OPCODE_GETELEMENTPTR:
                getElementInsts.append(istr)

    #process getelementptr instruction one by one
    for i in getElementInsts:
        stack = []
        level = 0
    
        #stack.append([i.operands[1],level])
        if i.opcode == OPCODE_GETELEMENTPTR:
            stack.append([i.operands[1],level])
        if i.opcode == OPCODE_STORE:
            stack.append([i.operands[0],level])

        stackptr = 0;
        stacklen = 1;
        while stackptr<stacklen:
            if isinstance(stack[stackptr][0],Instruction) == False:
                stackptr=stackptr+1
                continue
            if stack[stackptr][0].opcode == OPCODE_LOAD:
                stackptr=stackptr+1
                continue
            if stack[stackptr][0].operand_count==1:
                stack.append([stack[stackptr][0].operands[0],stack[stackptr][1]+1])
                stacklen=stacklen+1
            if stack[stackptr][0].operand_count==2:
                stack.append([stack[stackptr][0].operands[0],stack[stackptr][1]+1])
                stack.append([stack[stackptr][0].operands[1],stack[stackptr][1]+1])
                stacklen=stacklen+2
            stackptr=stackptr+1

        #debug only
        #for elm in stack:
        #   print elm[0]

        namestack = []
        levelstack = []
        for elm in stack:
            if isinstance(elm[0],Instruction):
                if elm[0].opcode == OPCODE_LOAD:
                    #load a varaible
                    if not elm[0].operands[0].name=='':
                        namestack.append(elm[0].operands[0].name)
                        # replace with store operands[0]
                        for bb_in in f.basic_blocks:
                            for istr_in in bb_in.instructions:
                                if istr_in.opcode == OPCODE_STORE and istr_in.operands[1].name == elm[0].operands[0].name and istr_in.operands[1].name == 'c':
                                        getElementInsts.append(istr_in)
                    #load an argument
                    else:
                        strStart = str(elm[0].operands[0]).find('%')
                        strEnd = str(elm[0].operands[0]).find('=')
                        argNum = str(elm[0].operands[0])[strStart+1:strEnd]
                        namestack.append(f.args[int(argNum)-1].name)
                else:
                    namestack.append(elm[0].opcode_name)
            elif isinstance(elm[0],ConstantInt):
                namestack.append(elm[0].z_ext_value)
            levelstack.append(elm[1])

        #print namestack  #debug only
        #print levelstack #debug only
        
        # convert the numbers in namestack into strings
        for index in range(0,stacklen):
            if isinstance(namestack[index], (int, long, float, complex)):
                namestack[index] = str(namestack[index])

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

        if not namestack[0] == '0':
            if i.opcode == OPCODE_GETELEMENTPTR:
                strStart = str(i.operands[0].operands[0]).find('%')
                strEnd = str(i.operands[0].operands[0]).find('=')
                argNum = str(i.operands[0].operands[0])[strStart+1:strEnd]
                resultEquations.append(f.args[int(argNum)-1].name + ' = ' + namestack[0])
                #add to getElementInstsCandidate to analysis constrains
                getElementInstsCandidate.append(i)
            if i.opcode == OPCODE_STORE:
                for index,rE in enumerate(resultEquations):
                    resultEquations[index]=rE.replace(i.operands[1].name,namestack[0])



print "Array access analysis result============="
for rE in resultEquations:
    print rE

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
